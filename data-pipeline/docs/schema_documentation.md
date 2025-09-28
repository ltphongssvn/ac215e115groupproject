# AirTable to PostgreSQL Schema Documentation

Base ID: `appmeTyHLozoqighD`
Discovered: 2025-09-27T00:54:01.041926

## Tables (6)

### Contracts (Hợp Đồng)
- Table ID: `tbl7sHbwOCOTjL2MC`
- Fields: 4
- Relationships: 0

#### Fields:
- **Received Quantity**: Unknown → INTEGER
- **Quantity Received at DN**: Unknown → INTEGER
- **Loss**: Unknown → INTEGER
- **Total Amount**: Unknown → INTEGER

### Contracts (Hợp Đồng) - 2
- Table ID: `tbllz4cazITSwnXIo`
- Fields: 17
- Relationships: 0

#### Fields:
- **Receipt Date**: Unknown → VARCHAR(255)
- **Receipt Number**: Unknown → VARCHAR(255)
- **Commodity Type**: Unknown → INTEGER[]
- **Unit Price**: Unknown → INTEGER
- **Logistics Cost (VC)**: Unknown → INTEGER
- **Total Price (with VC)**: Unknown → INTEGER
- **Received Quantity**: Unknown → INTEGER
- **Imported Quantity (ĐN)**: Unknown → INTEGER
- **Loss**: Unknown → INTEGER
- **Total Value**: Unknown → INTEGER
- **Protein (%)**: Unknown → DECIMAL(15,4)
- **Ash (%)**: Unknown → DECIMAL(15,4)
- **Fibre (%)**: Unknown → DECIMAL(15,4)
- **Fat (%)**: Unknown → DECIMAL(15,4)
- **Moisture (%)**: Unknown → DECIMAL(15,4)
- **Starch (%)**: Unknown → DECIMAL(15,4)
- **Acid Value (%)**: Unknown → INTEGER

### Customers
- Table ID: `tblDUfIlNy07Z0hiL`
- Fields: 3
- Relationships: 0

#### Fields:
- **Customer Name**: Unknown → VARCHAR(255)
- **National ID (CCCD)**: Unknown → VARCHAR(255)
- **Address**: Unknown → VARCHAR(255)

### Shipments
- Table ID: `tblSj7JcxYYfs6Dcl`
- Fields: 4
- Relationships: 0

#### Fields:
- **Commodity Type**: Unknown → INTEGER[]
- **Vehicle/Container Number**: Unknown → VARCHAR(255)
- **Delivered Quantity (kg)**: Unknown → INTEGER
- **Arrival Time**: Unknown → VARCHAR(255)

### Inventory Movements
- Table ID: `tblhb3Vxhi6Yt0BDw`
- Fields: 7
- Relationships: 0

#### Fields:
- **Date**: Unknown → DATE
- **Batch/Note**: Unknown → VARCHAR(255)
- **Vehicle/Container**: Unknown → VARCHAR(255)
- **LDH/KH**: Unknown → VARCHAR(255)
- **Commodity Type**: Unknown → INTEGER[]
- **Production Out (Tons)**: Unknown → INTEGER
- **Loss 1.3% (from 1/6/2025)**: Unknown → INTEGER

### Finished Goods
- Table ID: `tblNY26FnHswHRcWS`
- Fields: 10
- Relationships: 0

#### Fields:
- **Ngày nhập**: Unknown → VARCHAR(255)
- **LDH**: Unknown → VARCHAR(255)
- **Máy**: Unknown → VARCHAR(255)
- **Số lượng container**: Unknown → INTEGER
- **Số lượng theo đầu bao - Trong giờ**: Unknown → DECIMAL(15,4)
- **Số lượng theo đầu bao - Ngoài giờ**: Unknown → DECIMAL(15,4)
- **Tiền bồi dưỡng BX CONT (50K/20T, 100K/40T)**: Unknown → INTEGER
- **Tiền BX trong giờ (23K)**: Unknown → DECIMAL(15,4)
- **Ngoài giờ**: Unknown → DECIMAL(15,4)
- **Tổng (ca 1)**: Unknown → DECIMAL(15,4)