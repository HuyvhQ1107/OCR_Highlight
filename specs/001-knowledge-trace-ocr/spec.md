# Feature Specification: Dấu Vết Tri Thức (Knowledge Trace AI OCR)

**Feature Branch**: `001-knowledge-trace-ocr`

**Created**: 2026-11-16

**Status**: Draft

**Input**: User description: "Xây dựng hệ thống 'Dấu Vết Tri Thức' dựa trên De_tai_Dau_Vet_Tri_Thuc_AI_OCR.docx. Đầu vào: upload trực tiếp file PDF hoặc ảnh (.png, .jpg, .jpeg) đã tô màu highlight sẵn để hệ thống tự phát hiện vùng tô màu. Hỗ trợ Tiếng Việt + Tiếng Anh. Yêu cầu đăng nhập/tài khoản cá nhân và lưu lịch sử tra cứu. Tiêu chí định lượng MVP: file ≤ 20MB (≤ 50 trang scan / ≤ 100 trang PDF), OCR ≤ 3s/trang, tìm kiếm ≤ 1.5s, AI giải thích hoàn tất ≤ 15s, độ chính xác phát hiện highlight ≥ 85% và OCR ≥ 90%."

## Clarifications

### Session 2026-11-16

- Q: Khi người học tìm kiếm kiến thức đã đánh dấu trong phiên bản MVP, hệ thống nên hỗ trợ kiểu tìm kiếm nào? → A: Kết hợp tìm kiếm từ khóa và tìm kiếm theo ngữ nghĩa (semantic search) trên nội dung highlight.
- Q: Sau khi hệ thống phát hiện vùng highlight và trích xuất văn bản, người học có được phép chỉnh sửa nội dung văn bản OCR hoặc xóa vùng highlight/tài liệu đã tải lên không? → A: Chỉ cho phép xem và xóa toàn bộ tài liệu (không sửa/xóa từng vùng highlight).
- Q: Khi người học tải lên tài liệu PDF nhiều trang, hệ thống nên xử lý theo luồng nào? → A: Xử lý chạy nền bất đồng bộ, hiển thị trạng thái tiến trình và cho phép người học thao tác việc khác.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tài khoản cá nhân & Tải lên tài liệu học tập (Priority: P1)

Người học đăng ký/đăng nhập vào tài khoản cá nhân để tải lên tài liệu học tập (file PDF hoặc hình ảnh `.png`, `.jpg`, `.jpeg`) đã được tô màu highlight sẵn, đồng thời quản lý danh sách tài liệu và lịch sử tra cứu của riêng mình.

**Why this priority**: Đây là điểm khởi đầu bắt buộc để mọi dữ liệu tài liệu, vùng highlight và lịch sử tra cứu được gắn với từng cá nhân và bảo mật riêng tư.

**Independent Test**: Có thể kiểm thử độc lập bằng cách tạo tài khoản, đăng nhập, tải lên một file PDF hoặc ảnh hợp lệ, đăng xuất rồi đăng nhập lại để xác nhận tài liệu vẫn được lưu đúng trong kho cá nhân.

**Acceptance Scenarios**:

1. **Given** người học chưa có tài khoản, **When** người học đăng ký bằng email và mật khẩu hợp lệ rồi đăng nhập, **Then** hệ thống tạo tài khoản và cho phép truy cập không gian làm việc cá nhân.
2. **Given** người học đã đăng nhập, **When** người học tải lên một file PDF (≤ 100 trang, hoặc ≤ 50 trang đối với PDF scan) hoặc ảnh (`.png`, `.jpg`, `.jpeg`) có dung lượng ≤ 20 MB, **Then** hệ thống lưu trữ tài liệu vào hồ sơ cá nhân và hiển thị trạng thái sẵn sàng xử lý.
3. **Given** tài khoản A và tài khoản B đều có tài liệu riêng, **When** tài khoản A đăng nhập và xem danh sách tài liệu hoặc lịch sử tra cứu, **Then** hệ thống chỉ hiển thị dữ liệu thuộc về tài khoản A.

---

### User Story 2 - Tự động phát hiện vùng highlight & OCR song ngữ (Priority: P1)

Sau khi tài liệu được tải lên, hệ thống tự động quét từng trang để phát hiện các vùng đã được tô màu highlight và nhận diện nội dung văn bản (hỗ trợ Tiếng Việt và Tiếng Anh), kể cả trên tài liệu scan hoặc ảnh chụp không có lớp văn bản.

**Why this priority**: Phát hiện vùng tô màu và trích xuất văn bản chính xác là năng lực cốt lõi tạo nên "dấu vết tri thức" cho toàn bộ quy trình phía sau.

**Independent Test**: Có thể kiểm thử độc lập bằng cách tải lên một trang PDF scan hoặc ảnh chụp tài liệu có tô màu highlight Tiếng Việt và Tiếng Anh, sau đó kiểm tra danh sách các đoạn văn bản được hệ thống trích xuất kèm số trang.

**Acceptance Scenarios**:

1. **Given** người học tải lên tài liệu PDF hoặc ảnh có các đoạn văn bản đã tô màu highlight bằng Tiếng Việt hoặc Tiếng Anh, **When** hệ thống hoàn tất quá trình phân tích, **Then** hệ thống liệt kê được các vùng highlight phát hiện được cùng nội dung văn bản đã nhận diện và vị trí trang tương ứng.
2. **Given** tài liệu là bản scan hoặc ảnh chụp không có lớp văn bản sẵn, **When** hệ thống xử lý nhận diện, **Then** nội dung trong vùng highlight vẫn được trích xuất thành văn bản có thể đọc và tìm kiếm được.

---

### User Story 3 - Tìm kiếm & Truy hồi vị trí kiến thức trong tài liệu (Priority: P1)

Người học nhập từ khóa, cụm từ hoặc nội dung nhớ mang máng liên quan đến kiến thức đã đánh dấu để tìm lại chính xác vị trí xuất hiện trong tài liệu (số trang, đoạn văn và ngữ cảnh xung quanh), đồng thời hệ thống lưu lại lịch sử tra cứu.

**Why this priority**: Giải quyết trực tiếp nỗi đau chính của người học là "nhớ mình từng đánh dấu nhưng không nhớ nằm ở trang nào, ngữ cảnh nào".

**Independent Test**: Có thể kiểm thử độc lập bằng cách nhập một từ khóa nằm trong vùng highlight đã trích xuất và kiểm tra hệ thống trả về đúng tài liệu, số trang, đoạn văn chứa nội dung đó và ghi nhận vào lịch sử tra cứu.

**Acceptance Scenarios**:

1. **Given** tài liệu của người học đã được nhận diện vùng highlight, **When** người học tìm kiếm một từ khóa hoặc cụm từ xuất hiện trong vùng đã đánh dấu, **Then** hệ thống trả về danh sách kết quả gồm tên tài liệu, số trang, đoạn nội dung được đánh dấu và đoạn ngữ cảnh xung quanh.
2. **Given** người học thực hiện một lượt tìm kiếm, **When** kết quả được hiển thị, **Then** truy vấn và kết quả được lưu vào lịch sử tra cứu cá nhân để người học xem lại sau này.

---

### User Story 4 - Giải thích kiến thức theo ngữ cảnh tài liệu (Priority: P2)

Khi người học chọn một nội dung đã tìm thấy hoặc một vùng highlight, hệ thống phân tích đoạn kiến thức đó dựa trên ngữ cảnh của tài liệu để giải thích theo nhiều hình thức (cơ bản, chuyên sâu, ví dụ minh họa hoặc tóm tắt ngắn gọn).

**Why this priority**: Giúp người học không chỉ tìm lại được vị trí mà còn hiểu ngay kiến thức tại chỗ mà không phải đọc lại toàn bộ chương tài liệu.

**Independent Test**: Có thể kiểm thử độc lập bằng cách chọn một đoạn highlight bất kỳ đã truy hồi, yêu cầu giải thích ở từng chế độ (cơ bản, chuyên sâu, ví dụ minh họa, tóm tắt) và xác minh nội dung phản hồi bám sát ngữ cảnh tài liệu.

**Acceptance Scenarios**:

1. **Given** người học đang xem một kết quả tìm kiếm hoặc vùng highlight, **When** người học yêu cầu giải thích và chọn mức độ (cơ bản, chuyên sâu, ví dụ minh họa hoặc tóm tắt ngắn gọn), **Then** hệ thống hiển thị lời giải thích phù hợp với ngữ cảnh của đoạn tài liệu đó.
2. **Given** người học đã nhận được lời giải thích cho một vùng highlight, **When** người học mở lại vùng highlight đó trong lịch sử cá nhân, **Then** người học có thể xem lại hoặc yêu cầu giải thích lại theo chế độ khác.

---

### User Story 5 - Liên kết kiến thức & Hỗ trợ ôn tập (Priority: P3)

Hệ thống nhận diện các khái niệm liên quan giữa các nội dung đã đánh dấu để người học khám phá mối liên hệ kiến thức, và cho phép tạo câu hỏi kiểm tra ngắn (quiz) hoặc flashcard từ các nội dung đã truy hồi để ôn tập chủ động.

**Why this priority**: Chuyển việc tìm lại kiến thức thành hoạt động học tập chủ động, gia tăng giá trị giữ chân người học sau khi đã giải quyết xong bài toán tìm kiếm và giải thích.

**Independent Test**: Có thể kiểm thử độc lập bằng cách chọn một hoặc nhiều vùng highlight đã lưu, kích hoạt tính năng gợi ý liên kết hoặc tạo flashcard/quiz và kiểm tra bộ thẻ/câu hỏi được tạo ra.

**Acceptance Scenarios**:

1. **Given** người học có nhiều vùng highlight chứa các khái niệm liên quan trong tài liệu, **When** người học xem chi tiết một vùng highlight, **Then** hệ thống gợi ý các vùng highlight hoặc khái niệm liên quan khác trong kho tài liệu của người học.
2. **Given** người học chọn một hoặc nhiều nội dung kiến thức đã truy hồi, **When** người học chọn tạo nội dung ôn tập (flashcard hoặc câu hỏi kiểm tra ngắn), **Then** hệ thống sinh ra bộ flashcard (mặt trước/mặt sau) hoặc câu hỏi kèm đáp án dựa trên nội dung đã đánh dấu.

---

### Edge Cases

- **Tệp vượt giới hạn cho phép**: Khi người học tải lên tệp > 20 MB, PDF > 100 trang hoặc PDF scan > 50 trang, hệ thống từ chối xử lý và thông báo rõ giới hạn cụ thể.
- **Định dạng không hỗ trợ hoặc tệp lỗi**: Khi người học tải lên tệp ngoài `.pdf`, `.png`, `.jpg`, `.jpeg` hoặc tệp PDF bị hỏng/đặt mật khẩu bảo vệ, hệ thống báo lỗi rõ ràng và không lưu tệp lỗi.
- **Không phát hiện vùng highlight**: Khi tài liệu hoặc ảnh không có vùng tô màu highlight nào (hoặc ảnh quá mờ/lóa), hệ thống thông báo không tìm thấy vùng đánh dấu và gợi ý người học kiểm tra chất lượng ảnh/tài liệu.
- **Tài liệu song ngữ hoặc nhiều màu highlight**: Khi một trang có đồng thời Tiếng Việt, Tiếng Anh và nhiều màu highlight khác nhau, hệ thống vẫn nhận diện và tách riêng từng vùng đánh dấu mà không bỏ sót.
- **Tìm kiếm không có kết quả**: Khi từ khóa tìm kiếm không khớp với nội dung nào trong kho dấu vết của người học, hệ thống hiển thị thông báo trống thân thiện và gợi ý kiểm tra từ khóa hoặc phạm vi tài liệu.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST cho phép người học đăng ký tài khoản cá nhân, đăng nhập và đăng xuất để bảo vệ dữ liệu học tập riêng tư.
- **FR-002**: Hệ thống MUST cho phép người học đã đăng nhập tải lên tài liệu học tập định dạng `.pdf`, `.png`, `.jpg`, `.jpeg` với dung lượng tối đa 20 MB, tối đa 100 trang cho PDF có lớp văn bản và tối đa 50 trang cho PDF scan.
- **FR-003**: Hệ thống MUST tự động phát hiện các vùng nội dung đã được tô màu highlight trực tiếp trên file PDF và hình ảnh tải lên theo cơ chế xử lý chạy nền bất đồng bộ, cập nhật trạng thái tiến trình tài liệu (`Đang chờ` → `Đang xử lý` → `Sẵn sàng` hoặc `Lỗi`) để người học vẫn có thể sử dụng các tính năng khác trong lúc chờ.
- **FR-004**: Hệ thống MUST trích xuất nội dung văn bản từ các vùng highlight bằng khả năng nhận diện ký tự (OCR) hỗ trợ cả Tiếng Việt (có dấu đầy đủ) và Tiếng Anh, kể cả với tài liệu scan hoặc ảnh không có lớp văn bản.
- **FR-005**: Hệ thống MUST lưu trữ tài liệu và danh sách các vùng highlight đã trích xuất (kèm số trang và đoạn ngữ cảnh) gắn với từng tài khoản; người học có thể xem và xóa toàn bộ tài liệu (kèm dữ liệu highlight liên quan), không hỗ trợ chỉnh sửa hay xóa từng vùng highlight riêng lẻ trong MVP.
- **FR-006**: Hệ thống MUST cho phép người học tìm kiếm kết hợp cả từ khóa và ngữ nghĩa (semantic search) trên các nội dung đã đánh dấu, trả về vị trí chính xác gồm tài liệu nguồn, số trang, đoạn văn bản được highlight và ngữ cảnh xung quanh.
- **FR-007**: Hệ thống MUST lưu lại lịch sử tra cứu (từ khóa tìm kiếm, thời gian, kết quả đã xem) theo từng tài khoản người học và cho phép xem lại.
- **FR-008**: Hệ thống MUST hỗ trợ giải thích nội dung kiến thức đã tìm thấy dựa trên ngữ cảnh tài liệu theo các chế độ: giải thích cơ bản, giải thích chuyên sâu, ví dụ minh họa và tóm tắt ngắn gọn.
- **FR-009**: Hệ thống MUST có khả năng phát hiện và gợi ý các khái niệm/vùng highlight liên quan giữa các nội dung người học đã đánh dấu.
- **FR-010**: Hệ thống MUST cho phép tạo học liệu ôn tập dưới dạng flashcard hoặc câu hỏi kiểm tra ngắn (quiz) kèm đáp án từ các nội dung kiến thức đã truy hồi.
- **FR-011**: Hệ thống MUST cô lập hoàn toàn dữ liệu tài liệu, vùng highlight và lịch sử tra cứu giữa các tài khoản khác nhau.

### Key Entities *(include if feature involves data)*

- **Tài khoản người học (User Account)**: Đại diện cho người dùng cá nhân; gồm thông tin định danh đăng nhập, hồ sơ cơ bản và quyền sở hữu đối với tài liệu, dấu vết và lịch sử tra cứu.
- **Tài liệu (Document)**: Tệp PDF hoặc ảnh do người học tải lên; gồm tên tệp, định dạng, dung lượng, số trang, trạng thái xử lý (`Đang chờ`, `Đang xử lý`, `Sẵn sàng`, `Lỗi`) và liên kết tới chủ sở hữu.
- **Dấu vết Highlight (Highlight Trace)**: Một vùng nội dung được tô màu phát hiện từ tài liệu; gồm nội dung văn bản đã OCR, số trang, vị trí vùng chọn, đoạn ngữ cảnh xung quanh và ngôn ngữ nhận diện.
- **Lịch sử tra cứu (Search History)**: Bản ghi mỗi lượt tìm kiếm hoặc truy hồi của người học; gồm nội dung truy vấn, thời điểm tra cứu và các dấu vết liên quan đã mở.
- **Giải thích kiến thức (Knowledge Explanation)**: Nội dung giải thích được tạo cho một dấu vết highlight theo ngữ cảnh và mức độ yêu cầu (cơ bản, chuyên sâu, ví dụ, tóm tắt).
- **Học liệu ôn tập (Study Material)**: Bộ flashcard hoặc câu hỏi kiểm tra ngắn được tạo từ một hoặc nhiều dấu vết highlight để phục vụ ôn tập.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Hệ thống phát hiện chính xác tối thiểu **85%** các vùng đã tô màu highlight trên tài liệu PDF và ảnh chụp/scan rõ nét (≥ 150 DPI, không bị lóa/mờ).
- **SC-002**: Độ chính xác nhận diện ký tự (OCR) trong vùng highlight đạt tối thiểu **90%** đối với cả Tiếng Việt và Tiếng Anh trên tài liệu rõ nét.
- **SC-003**: Thời gian xử lý phát hiện vùng highlight và OCR không vượt quá **3 giây mỗi trang** đối với tài liệu ảnh/scan.
- **SC-004**: **95%** lượt tìm kiếm truy hồi vị trí kiến thức trả về kết quả trong vòng **≤ 1.5 giây**.
- **SC-005**: Yêu cầu giải thích kiến thức theo ngữ cảnh hoàn tất phản hồi trong vòng **≤ 15 giây**.
- **SC-006**: Hệ thống hỗ trợ xử lý ổn định các tệp tài liệu trong ngưỡng quy định (**≤ 20 MB**, **≤ 50 trang scan** hoặc **≤ 100 trang PDF**) mà không bị lỗi mất dữ liệu.
- **SC-007**: Người học có thể hoàn tất luồng cốt lõi (đăng nhập → tải tài liệu → xem vùng highlight trích xuất → tìm kiếm → xem giải thích) ở lần sử dụng đầu tiên trong vòng **dưới 5 phút** với tài liệu mẫu 5–10 trang.

## Assumptions

- Người học sử dụng tài liệu rõ nét ở mức đọc được bằng mắt thường (khuyến nghị từ 150 DPI trở lên đối với ảnh chụp/scan) và sử dụng các màu highlight phổ biến có độ tương phản rõ với nền giấy/chữ.
- Xác thực mặc định cho MVP sử dụng cặp email và mật khẩu tiêu chuẩn.
- Các tính năng thuộc giai đoạn mở rộng trong tài liệu đề xuất (hỗ trợ Word `.docx`, PowerPoint `.pptx`, Chrome Extension highlight trực tiếp trên web, bản đồ tri thức Knowledge Graph hoàn chỉnh, nhận diện công thức toán học chuyên sâu) nằm ngoài phạm vi MVP này.
- Việc đánh giá chất lượng giải thích và học liệu ôn tập tập trung vào tính đúng ngữ cảnh tài liệu và khả năng hỗ trợ học tập, giả định người học có kết nối mạng ổn định khi sử dụng hệ thống.
