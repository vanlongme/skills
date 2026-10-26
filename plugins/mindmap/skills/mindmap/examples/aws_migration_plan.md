# Kế hoạch di chuyển lên AWS

## Đánh giá hiện trạng
- Kiểm kê ứng dụng
  - VMware vSphere
  - Proxmox · RKE2
- Phân loại 7R
  - Rehost
  - Replatform
  - Refactor
- Ước tính chi phí TCO

## Nền tảng (landing zone)
- Control Tower + AFT
- Network account
  - Direct Connect × 2
  - Transit Gateway
- Security · Log archive

## Di chuyển theo đợt
- Đợt 1: ứng dụng nội bộ
- Đợt 2: hệ thống khách hàng
- Đợt 3: dữ liệu lớn
  - Oracle → RDS
  - SQL Server → RDS

## Vận hành
- FinOps · tagging
- Giám sát tập trung
- Đào tạo đội ngũ
- Giữ lại on-prem {collapsed}
  - HSM
  - Core banking
