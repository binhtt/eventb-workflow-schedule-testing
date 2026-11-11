# Thực nghiệm mở rộng cho workflow multi-agent

Ngày chạy 06/11/2026.

## Ba phần đã thực hiện

**Sinh mục tiêu từ Event-B.** Bộ đọc XML lấy guard và phép gán từ Resource.bum,
phân tích cây biểu thức, xác định biến được đọc trong guard và biến được ghi
trong action. Các phép thêm/xóa singleton được phân biệt theo request, còn
các biến số học dùng chung có phạm vi toàn cục. Hai thao tác tạo thành một
mục tiêu khi action của một thao tác có thể ảnh hưởng guard của thao tác kia.
Bộ sinh xây tiền tố hợp lệ để hai guard cùng đúng, sau đó xen validation và
apply để thử khả năng tái kiểm tra điều kiện. Những mục tiêu không có tiền
tố phù hợp bị bỏ qua. Phần còn thiếu ngân sách được bổ sung bằng lấy mẫu.

Hook, liên kết hook với event và thứ tự giao thức nằm trong adapter viết tay.
Bộ sinh không đọc tên mutant. Bộ đọc hỗ trợ tập cú pháp được nêu trong mã,
và báo lỗi với cú pháp ngoài phạm vi. Đây là tự động hóa sinh mục tiêu từ
guard/action với adapter, chưa phải chuyển đổi tự động mọi mô hình Event-B
thành một bộ kiểm thử.

**Case study có tài nguyên chung.** Nhiều request cạnh tranh đặt chỗ trên
pool giới hạn CAP. Mỗi request có hai lần thử reserve, hai lần thử execute,
chuyển giao giữa hai epoch của worker, acknowledgement, release và expiry.
Điều kiện quan trọng là số chỗ tự do cộng số lease đang giữ bằng CAP,
request đóng không tiếp tục giữ chỗ, tác động không bị lặp và token cũ bị
từ chối ở thời điểm sử dụng. Expiry là thao tác môi trường được phép sau
reservation. Case study dùng thứ tự sự kiện, không mô hình hóa thời gian thực.

**Implementation và lỗi đánh giá.** Service SQLite lưu pool, lease, trạng
thái kết thúc, handover, tác động và acknowledgement trong các bảng riêng.
Mã service không import mô hình hay bộ sinh. Oracle đối chiếu trạng thái
sau apply với ngữ nghĩa XML, đồng thời audit DB và các tác động được ghi
nhận. Tập lỗi gồm ba mutant phát triển và sáu mutant dành cho đánh giá.
Cùng tác giả xây dựng các thành phần, vì vậy phép chia này là tách mutant
implementation, chưa phải đánh giá mù độc lập hoặc tách hoàn toàn họ lỗi.

## Chứng minh hình thức

Mô hình mới SharedWorkflow tham số hóa theo tập REQ hữu hạn và CAP nguyên
dương. Rodin 3.9 kiểm tra tĩnh thành công và tự động discharge **24/24 PO**.

| Loại nghĩa vụ | Số lượng | Đã discharge |
|---|---:|---:|
| Bảo toàn bất biến, INV | 15 | 15 |
| Bổ đề, THM | 6 | 6 |
| Tính xác định biểu thức, WD | 3 | 3 |
| Tổng | 24 | 24 |

Proof được tạo từ nguồn với các proof lưu sẵn đã purge, dùng profile kết hợp
tactic mặc định, PP và Atelier B PP/ML. Mọi status được lưu là automatic,
manual=false. Định lý về finite và cardinality phục vụ bảo toàn tài nguyên
được chứng minh bằng công cụ.

Trong Release/Expire, bản phục vụ proof đặt tên tập còn lại bằng tham số
remaining = held ∖ {r}, rồi chứng minh các bổ đề phân hoạch và cardinality.
proof_bridge.py thay thế tham số được định nghĩa duy nhất, bỏ các guard
theorem đã được chứng minh và xác nhận cây cú pháp guard/action trùng khớp
với mô hình dùng khi đánh giá. Context cũng giống hệt. Kiểm tra tái sinh
cho kết quả giống nhau ở **600 bộ lịch, tổng 9.600 lịch**.

Các PO của mô hình tài nguyên chung này độc lập với 53 PO của mô hình
single-request trước. Mô hình mới chứng minh các bất biến đã khai báo và
định nghĩa guard của Execute loại request đã tạo tác động. Nó không có
nghĩa vụ refinement sang service SQLite hay nghĩa vụ liveness vô hạn.

## Đối chiếu toàn bộ instance nhỏ

| Request / capacity | Trạng thái | Chuyển hợp lệ | Lần gọi bị từ chối | Tổng lần gọi đối chiếu |
|---|---:|---:|---:|---:|
| 1 / 1 | 13 | 26 | 78 | 104 |
| 2 / 1 | 133 | 412 | 1.716 | 2.128 |
| 3 / 2 | 1.981 | 10.806 | 36.738 | 47.544 |
| Tổng | 2.127 | 11.244 | 38.532 | 49.776 |

Các không gian trạng thái trên đã được duyệt hết. Mọi lần gọi, gồm cả epoch
0 và 1 của Execute/Acknowledge, có kết quả chấp nhận/từ chối và trạng thái
khớp giữa XML và SQLite. Bộ kiểm tra độc lập này dùng ngữ nghĩa thực thi
của tập con Event-B. Tính đúng tổng quát của bộ dịch không được chứng minh
bằng Rodin.

## Thiết kế đánh giá lịch

Ba cấu hình request/capacity là 2/1, 4/2 và 8/3. Mỗi cấu hình có 50 seed,
bốn phương pháp và ngân sách 16 lịch. Các mốc 1, 2, 4 và 8 là tiền tố của
cùng bộ lịch. Mỗi lịch được chạy trên bản đúng và đủ chín mutant, kể cả
sau khi đã phát hiện lỗi.

Đã chạy **9.600 replay bản đúng** và **86.400 replay mutant** trong lượt
chính. Bản đúng qua toàn bộ kiểm tra thuộc tính và conformance. Tổng số
apply của bản đúng được đối chiếu trong lượt chính là 358.400.

- Nominal lặp lại lịch tuần tự mặc định, có một lịch phân biệt.
- Random chọn đều trong các hook đang enabled, có thể lặp lịch.
- Model conflicts dùng các mục tiêu interference từ Event-B.
- Canonical independence dùng sleep-set DFS. Chỉ probe/probe được xem là
  độc lập, các apply được giữ phụ thuộc để không dựa vào footprint của
  một implementation có thể đang bị lỗi.

Baseline reduction giữ đủ bốn lớp trong fixture kiểm tra có sáu lịch thô.
Trạng thái cuối và verdict của các lịch được gộp đều khớp ở cả bản đúng
và chín mutant. Trong case lớn, thứ tự DFS khiến các lịch đầu có thể rất
giống nhau. Các số liệu của baseline này không đại diện cho mọi DPOR.

## Phân loại lỗi và denominator

| Mutant đánh giá | Hành vi | Trạng thái |
|---|---|---|
| reserve_lost_update | Ghi lại số chỗ từ snapshot cũ | Qua nominal, dùng trong đánh giá temporal |
| release_wrong_key | Trả chỗ của request khác khi request đó đang giữ lease | Qua nominal, loại cấu hình CAP=1 vì nhánh lỗi không thể kích hoạt |
| execute_after_release | Dùng validation cũ sau khi lease đã bị thu hồi | Qua nominal, dùng trong đánh giá temporal |
| execute_old_epoch | Bỏ kiểm tra epoch khi execute | Qua nominal, dùng trong đánh giá temporal |
| transfer_credit | Cộng nhầm chỗ tự do khi handoff | Lộ ở nominal, báo riêng |
| ack_old_epoch | Chấp nhận ACK của epoch cũ | Lộ ở nominal, báo riêng |

Raw CSV giữ toàn bộ lỗi và cấu hình. Việc qualification được áp dụng ở
bước phân tích và được ghi rõ trong analyse.py. Denominator temporal là
**550 tổ hợp seed–mutant–cấu hình**, gồm 50 seed cho 11 tổ hợp
mutant/cấu hình hợp lệ. Đây là bốn mutant, không phải 550 lỗi độc lập.

## Kết quả temporal đã qualification

| Request / capacity | Phương pháp | Phát hiện sau 4 lịch | Phát hiện sau 16 lịch |
|---|---|---:|---:|
| 2 / 1 | Nominal | 0/150 | 0/150 |
| 2 / 1 | Random | 94/150 | 146/150 |
| 2 / 1 | Model conflicts | 103/150 | 150/150 |
| 2 / 1 | Canonical independence | 25/150 | 25/150 |
| 4 / 2 | Nominal | 0/200 | 0/200 |
| 4 / 2 | Random | 189/200 | 200/200 |
| 4 / 2 | Model conflicts | 186/200 | 200/200 |
| 4 / 2 | Canonical independence | 88/200 | 88/200 |
| 8 / 3 | Nominal | 0/200 | 0/200 |
| 8 / 3 | Random | 197/200 | 200/200 |
| 8 / 3 | Model conflicts | 196/200 | 200/200 |
| 8 / 3 | Canonical independence | 156/200 | 156/200 |

Gộp các cấu hình, Model conflicts đạt **485/550** sau bốn lịch, Random
đạt **480/550**. Sau 16 lịch, các số tương ứng là **550/550** và
**546/550**. Chênh lệch sau bốn lịch là 0,91 điểm phần trăm, khoảng tin
cậy bootstrap 95% từ **−1,82 đến 3,64**. Dữ liệu chưa xác nhận ưu thế
nhất quán của cách sinh từ mô hình trên Random ở ngân sách này.

Bootstrap ghép cặp theo seed và resample cả block seed qua các cấu hình
và mutant, gồm 10.000 lần resample. Các khoảng là phân tích thăm dò,
chưa hiệu chỉnh cho việc xem nhiều ngân sách. Toàn bộ mốc được báo trong
paired_bootstrap.csv, thay vì chỉ chọn mốc có lợi.

## Chi phí

Timing riêng chạy 30 lần lặp cho mỗi phương pháp/cấu hình, seed 1000–1029,
và xáo trộn thứ tự phương pháp ở mỗi lần lặp. Mỗi phép đo gồm sinh đủ
16 lịch và replay bản đúng với kiểm tra conformance. Các lượt timing thêm
5.760 replay bản đúng, đều pass. Máy container có CPU Xeon Platinum 8573C,
9 CPU logic nhìn thấy, giới hạn RAM 8 GiB, Python 3.12.14, SQLite 3.53.1.
Không pin CPU. Timing phản ánh môi trường container dùng chung.

| Request / capacity | Random, thời gian trọn bộ 16 lịch | Model conflicts, thời gian trọn bộ 16 lịch |
|---|---:|---:|
| 2 / 1 | 26,39 ms | 33,30 ms |
| 4 / 2 | 51,38 ms | 64,57 ms |
| 8 / 3 | 109,95 ms | 155,93 ms |

Các giá trị là median. Chi phí gồm tạo prefix và kiểm tra feasibility của
mục tiêu, khởi tạo/reset DB và oracle. Không gồm chứng minh Rodin hay nạp
mô hình một lần. Thời gian sinh lịch riêng và thời gian replay nằm trong CSV.

## Phạm vi kết luận cho bản thảo

Có thể báo cáo một pipeline có nguồn mô hình cụ thể, mục tiêu được trích
từ guard/action, case study có tranh chấp tài nguyên, proof Rodin thật,
đối chiếu implementation và đánh giá mutant được phân loại theo nominal.

Dữ liệu cho thấy phương pháp sinh lịch có thể phát hiện đủ các mutant
temporal được đánh giá trong ngân sách 16 lịch. Tại ngân sách bốn lịch,
chênh lệch với Random nhỏ và chưa rõ ràng, trong khi chi phí sinh lịch cao
hơn. Bài viết cần giữ phạm vi kết luận này. Hiện chỉ có một case study tự
xây dựng, chưa có benchmark bên ngoài, nền tảng agent thực tế hoặc đánh giá
LLM. Các mục tiêu cần adapter và tập cú pháp được hỗ trợ.
