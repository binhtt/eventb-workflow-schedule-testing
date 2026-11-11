"""SQLite implementation under test. Contains no Event-B imports."""
import sqlite3

MUTANTS = (
    'reserve_cached','execute_cached','release_cached',
    'reserve_lost_update','release_wrong_key','execute_after_release',
    'execute_old_epoch','transfer_credit','ack_old_epoch',
)

class Service:
    def __init__(self,size,capacity,mutant=None):
        self.size=size
        self.capacity=capacity
        self.mutant=mutant
        self.db=sqlite3.connect(':memory:')
        self.db.executescript("""
            CREATE TABLE pool(available INTEGER NOT NULL);
            CREATE TABLE leases(request INTEGER PRIMARY KEY);
            CREATE TABLE terminated(request INTEGER PRIMARY KEY);
            CREATE TABLE handovers(request INTEGER PRIMARY KEY);
            CREATE TABLE effects(request INTEGER);
            CREATE TABLE acknowledgements(request INTEGER PRIMARY KEY);
        """)
        self.db.execute('INSERT INTO pool VALUES (?)',(capacity,))
        self.cached={}
    def present(self,table,request):
        # Table names are fixed by the implementation.
        return self.db.execute(f'SELECT 1 FROM {table} WHERE request=?',(request,)).fetchone() is not None
    def available(self):
        return self.db.execute('SELECT available FROM pool').fetchone()[0]
    def valid(self,action,request,epoch):
        held=self.present('leases',request)
        if action=='Reserve':
            return not held and not self.present('terminated',request) and self.available()>0
        if action=='Execute':
            return held and not self.present('effects',request) and epoch==int(self.present('handovers',request))
        if action=='Transfer':
            return held and not self.present('handovers',request)
        if action=='Acknowledge':
            return self.present('effects',request) and epoch==int(self.present('handovers',request))
        if action in ('Release','Expire'):
            return held
        raise ValueError(action)
    def probe(self,operation):
        self.cached[operation.identity]=(self.valid(operation.action,operation.request,operation.epoch),
                                          self.available())
    def apply(self,operation):
        action,request,epoch=operation.action,operation.request,operation.epoch
        cached,cached_free=self.cached[operation.identity]
        accepted=self.valid(action,request,epoch)
        if self.mutant=='reserve_cached' and action=='Reserve':
            accepted=cached
        elif self.mutant=='execute_cached' and action=='Execute':
            accepted=cached
        elif self.mutant=='release_cached' and action in ('Release','Expire'):
            accepted=cached
        elif self.mutant=='execute_after_release' and action=='Execute':
            accepted=(cached and not self.present('effects',request)
                      and epoch==int(self.present('handovers',request)))
        elif self.mutant=='execute_old_epoch' and action=='Execute':
            accepted=self.present('leases',request) and not self.present('effects',request)
        elif self.mutant=='ack_old_epoch' and action=='Acknowledge':
            accepted=self.present('effects',request)
        observations=[]
        if not accepted:
            return False,observations
        with self.db:
            if action=='Reserve':
                self.db.execute('INSERT OR IGNORE INTO leases VALUES (?)',(request,))
                if self.mutant=='reserve_lost_update':
                    self.db.execute('UPDATE pool SET available=?',(cached_free-1,))
                else:
                    self.db.execute('UPDATE pool SET available=available-1')
            elif action=='Execute':
                observations.append(('effect',request,int(self.present('leases',request)),
                                     epoch,int(self.present('handovers',request))))
                self.db.execute('INSERT INTO effects VALUES (?)',(request,))
            elif action=='Transfer':
                self.db.execute('INSERT INTO handovers VALUES (?)',(request,))
                if self.mutant=='transfer_credit':
                    self.db.execute('UPDATE pool SET available=available+1')
            elif action=='Acknowledge':
                observations.append(('ack',request,epoch,int(self.present('handovers',request))))
                self.db.execute('INSERT OR IGNORE INTO acknowledgements VALUES (?)',(request,))
            else:
                victim=request
                if self.mutant=='release_wrong_key':
                    other=(request+1)%self.size
                    if self.present('leases',other):
                        victim=other
                self.db.execute('DELETE FROM leases WHERE request=?',(victim,))
                self.db.execute('INSERT OR IGNORE INTO terminated VALUES (?)',(request,))
                self.db.execute('UPDATE pool SET available=available+1')
        return True,observations
    def snapshot(self):
        def keys(table):
            return frozenset(row[0] for row in self.db.execute(f'SELECT request FROM {table}'))
        return {'REQ':frozenset(range(self.size)),'CAP':self.capacity,
                'free':self.available(),'held':keys('leases'),'closed':keys('terminated'),
                'moved':keys('handovers'),'effected':keys('effects'),'acked':keys('acknowledgements')}
    def audit(self,observations):
        """Independent property checks on persistent state and external effects."""
        failures=[]
        held=self.db.execute('SELECT COUNT(*) FROM leases').fetchone()[0]
        if self.available()<0: failures.append('negative_capacity')
        if self.available()+held!=self.capacity: failures.append('resource_conservation')
        if self.db.execute('SELECT 1 FROM leases JOIN terminated USING(request) LIMIT 1').fetchone():
            failures.append('closed_request_holds_resource')
        if self.db.execute('SELECT 1 FROM effects GROUP BY request HAVING COUNT(*)>1 LIMIT 1').fetchone():
            failures.append('duplicate_effect')
        for observation in observations:
            if observation[0]=='effect':
                _,_,has_lease,used_epoch,current_epoch=observation
                if not has_lease: failures.append('effect_without_reservation')
                if used_epoch!=current_epoch: failures.append('stale_execution')
            elif observation[0]=='ack' and observation[2]!=observation[3]:
                failures.append('stale_ack')
        return failures
    def close(self):
        self.db.close()
