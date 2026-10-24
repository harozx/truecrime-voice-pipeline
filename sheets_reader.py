"""
Google Sheets Reader Module
Đọc dữ liệu từ Google Sheets để lấy danh sách công việc cần xử lý
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

import config

# Tên file credentials
CREDENTIALS_FILE = config.CREDENTIALS_FILE

# Scopes cần thiết (cần quyền ghi để cập nhật status)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]


class SheetsReader:
    """Class để đọc Google Sheets"""
    
    def __init__(self, credentials_file=CREDENTIALS_FILE):
        """
        Khởi tạo Sheets Reader
        
        Args:
            credentials_file: Đường dẫn đến file credentials JSON
        """
        self.credentials_file = credentials_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Xác thực với Google Sheets API"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=SCOPES
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            print("✅ Xác thực thành công!")
        except Exception as e:
            print(f"❌ Lỗi xác thực: {str(e)}")
            raise
    
    def get_spreadsheet_info(self, spreadsheet_id):
        """
        Lấy thông tin cơ bản về spreadsheet
        
        Args:
            spreadsheet_id: ID của spreadsheet
            
        Returns:
            Dictionary chứa thông tin spreadsheet
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            info = {
                'title': spreadsheet.get('properties', {}).get('title'),
                'sheets': []
            }
            
            # Lấy danh sách các sheet
            for sheet in spreadsheet.get('sheets', []):
                sheet_props = sheet.get('properties', {})
                info['sheets'].append({
                    'id': sheet_props.get('sheetId'),
                    'title': sheet_props.get('title'),
                    'index': sheet_props.get('index'),
                    'row_count': sheet_props.get('gridProperties', {}).get('rowCount'),
                    'col_count': sheet_props.get('gridProperties', {}).get('columnCount')
                })
            
            return info
        except Exception as e:
            print(f"❌ Lỗi khi lấy thông tin spreadsheet: {str(e)}")
            return None
    
    def read_range(self, spreadsheet_id, range_name):
        """
        Đọc dữ liệu từ một range cụ thể
        
        Args:
            spreadsheet_id: ID của spreadsheet
            range_name: Range cần đọc (VD: 'Sheet1!A1:D10')
            
        Returns:
            List of lists chứa dữ liệu
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return values
        except Exception as e:
            print(f"❌ Lỗi khi đọc range '{range_name}': {str(e)}")
            return None
    
    def read_all_sheets(self, spreadsheet_id):
        """
        Đọc tất cả dữ liệu từ tất cả các sheet
        
        Args:
            spreadsheet_id: ID của spreadsheet
            
        Returns:
            Dictionary với key là tên sheet, value là dữ liệu
        """
        info = self.get_spreadsheet_info(spreadsheet_id)
        if not info:
            return None
        
        all_data = {}
        
        for sheet in info['sheets']:
            sheet_name = sheet['title']
            print(f"📄 Đọc sheet: {sheet_name}")
            
            # Đọc toàn bộ sheet
            data = self.read_range(spreadsheet_id, f"'{sheet_name}'")
            all_data[sheet_name] = data
        
        return all_data
    
    def print_sheet_data(self, data, max_rows=10):
        """
        In dữ liệu sheet ra console (dùng để debug)
        
        Args:
            data: Dictionary từ read_all_sheets()
            max_rows: Số dòng tối đa hiển thị
        """
        for sheet_name, rows in data.items():
            print(f"\n{'='*60}")
            print(f"📊 SHEET: {sheet_name}")
            print(f"{'='*60}")
            
            if not rows:
                print("  (Trống)")
                continue
            
            for i, row in enumerate(rows[:max_rows]):
                print(f"  Dòng {i+1}: {row}")
            
            if len(rows) > max_rows:
                print(f"  ... và {len(rows) - max_rows} dòng nữa")
    
    def update_cell(self, spreadsheet_id, range_name, value):
        """
        Cập nhật giá trị của một cell
        
        Args:
            spreadsheet_id: ID của spreadsheet
            range_name: Range cần update (VD: 'Sheet1!A1')
            value: Giá trị mới
            
        Returns:
            True nếu thành công, False nếu lỗi
        """
        try:
            body = {
                'values': [[value]]
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            return True
        except Exception as e:
            print(f"❌ Lỗi khi cập nhật cell '{range_name}': {str(e)}")
            return False
    
    def batch_update_cells(self, spreadsheet_id, updates):
        """
        Cập nhật nhiều cells cùng lúc
        
        Args:
            spreadsheet_id: ID của spreadsheet
            updates: List of dicts với format:
                     [{'range': 'Sheet1!E2', 'value': 'Not Started'}, ...]
        
        Returns:
            True nếu thành công, False nếu lỗi
        """
        try:
            data = []
            for update in updates:
                data.append({
                    'range': update['range'],
                    'values': [[update['value']]]
                })
            
            body = {
                'valueInputOption': 'RAW',
                'data': data
            }
            
            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            print(f"✅ Đã cập nhật {len(updates)} cells")
            return True
        except Exception as e:
            print(f"❌ Lỗi khi batch update: {str(e)}")
            return False
    
    def get_pending_videos(self, spreadsheet_id, sheet_name, batch_size=10):
        """
        Tìm các video có status "Not Started" và đánh dấu chúng là "In Progress"
        
        Args:
            spreadsheet_id: ID của spreadsheet
            sheet_name: Tên sheet
            batch_size: Số lượng video cần lấy (mặc định 10)
        
        Returns:
            List of dicts: [{'row': 2, 'stt': '1', 'link': 'https://...', 'title_vi': '...'}, ...]
        """
        try:
            # Đọc toàn bộ sheet
            data = self.read_range(spreadsheet_id, f"'{sheet_name}'")
            
            if not data or len(data) < 2:
                print("❌ Sheet trống hoặc không có dữ liệu")
                return []
            
            # Bỏ qua header (dòng đầu tiên)
            pending_videos = []
            
            for i, row in enumerate(data[1:], start=2):  # Bắt đầu từ dòng 2
                # Kiểm tra xem có đủ cột không
                if len(row) <= 4:  # Cột E (index 4) là trạng thái
                    # Không có trạng thái (cột trống hoặc không tồn tại)
                    status = ''
                else:
                    status = row[4].strip() if len(row) > 4 else ''
                
                # Chỉ lấy videos có trạng thái "Not Started"
                if status == 'Not Started':
                    # Lấy thông tin
                    stt = row[0] if len(row) > 0 else ''
                    link = row[1] if len(row) > 1 else ''
                    title_vi = row[3] if len(row) > 3 else ''
                    
                    # Validate YouTube link
                    if link and ('youtube.com' in link or 'youtu.be' in link):
                        pending_videos.append({
                            'row': i,
                            'stt': stt,
                            'link': link,
                            'title_vi': title_vi
                        })
                        
                        # Dừng khi đủ batch_size
                        if len(pending_videos) >= batch_size:
                            break
            
            if pending_videos:
                print(f"\n✅ Tìm thấy {len(pending_videos)} video có status 'Not Started'")
                
                # Cập nhật status thành "In Progress" cho tất cả videos tìm được
                updates = []
                for video in pending_videos:
                    row_num = video['row']
                    updates.append({
                        'range': f"'{sheet_name}'!E{row_num}",  # Cột E = Trạng thái
                        'value': 'In Progress'
                    })
                
                # Thực hiện batch update
                if self.batch_update_cells(spreadsheet_id, updates):
                    print(f"✅ Đã đánh dấu {len(pending_videos)} video là 'In Progress'")
                
                return pending_videos
            else:
                print("ℹ️ Không tìm thấy video nào có status 'Not Started'")
                return []
                
        except Exception as e:
            print(f"❌ Lỗi khi lấy pending videos: {str(e)}")
            return []
    
    def mark_video_completed(self, spreadsheet_id, sheet_name, row_number):
        """
        Đánh dấu một video là Completed
        
        Args:
            spreadsheet_id: ID của spreadsheet
            sheet_name: Tên sheet
            row_number: Số dòng cần update (1-indexed)
        
        Returns:
            True if success, False if failed
        """
        try:
            range_name = f"'{sheet_name}'!E{row_number}"
            return self.update_cell(spreadsheet_id, range_name, 'Completed')
        except Exception as e:
            print(f"❌ Lỗi khi đánh dấu completed: {str(e)}")
            return False




def get_service_account_email():
    """Hiển thị email của Service Account"""
    try:
        with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
            creds = json.load(f)
            email = creds.get('client_email')
            return email
    except Exception as e:
        print(f"Lỗi: {e}")
        return None


if __name__ == "__main__":
    print("🚀 GOOGLE SHEETS READER\n")
    
    # Hiển thị Service Account email
    email = get_service_account_email()
    print("=" * 60)
    print("📧 SERVICE ACCOUNT EMAIL:")
    print(email)
    print("=" * 60)
    print("QUAN TRỌNG: Chia sẻ spreadsheet với email trên!")
    print("=" * 60)
    
    # Spreadsheet ID lấy từ .env
    SPREADSHEET_ID = config.SPREADSHEET_ID
    
    print(f"\n📊 Đang đọc spreadsheet...")
    print(f"ID: {SPREADSHEET_ID}\n")
    
    # Khởi tạo reader
    reader = SheetsReader()
    
    # Lấy thông tin spreadsheet
    info = reader.get_spreadsheet_info(SPREADSHEET_ID)
    
    if info:
        print(f"✅ Tiêu đề: {info['title']}")
        print(f"📋 Số lượng sheets: {len(info['sheets'])}")
        print("\nDanh sách sheets:")
        for sheet in info['sheets']:
            print(f"  - {sheet['title']} ({sheet['row_count']} dòng x {sheet['col_count']} cột)")
        
        # Đọc tất cả dữ liệu
        print("\n" + "="*60)
        print("ĐANG ĐỌC DỮ LIỆU...")
        print("="*60)
        all_data = reader.read_all_sheets(SPREADSHEET_ID)
        
        if all_data:
            reader.print_sheet_data(all_data, max_rows=20)
            print("\n✅ ĐỌC DỮ LIỆU THÀNH CÔNG!")
    else:
        print("\n❌ KHÔNG THỂ TRUY CẬP SPREADSHEET!")
        print("Hãy chắc chắn rằng bạn đã:")
        print(f"1. Chia sẻ spreadsheet với: {email}")
        print("2. Cho quyền Viewer hoặc Editor")
        print("3. Document ID chính xác")
