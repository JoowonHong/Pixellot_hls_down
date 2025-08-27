import cv2
import os

def merge_mp4_files(video_files, output_file):
    """
    OpenCV를 사용해서 여러 mp4 파일을 합치기
    
    Args:
        video_files: 합칠 mp4 파일 리스트
        output_file: 출력할 mp4 파일명
    """
    try:
        # 첫 번째 비디오를 열어서 정보 확인
        first_cap = cv2.VideoCapture(video_files[0])
        if not first_cap.isOpened():
            print(f"❌ 첫 번째 파일을 열 수 없습니다: {video_files[0]}")
            return False
        
        # 비디오 정보 가져오기
        width = int(first_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(first_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = first_cap.get(cv2.CAP_PROP_FPS)
        
        print(f"비디오 정보: {width}x{height}, FPS: {fps}")
        
        # 비디오 작성기 설정
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
        
        if not out.isOpened():
            print(f"❌ 출력 파일을 생성할 수 없습니다: {output_file}")
            first_cap.release()
            return False
        
        first_cap.release()
        
        # 각 비디오 파일을 순서대로 합치기
        total_frames = 0
        for i, video_file in enumerate(video_files):
            print(f"처리 중: {video_file} ({i+1}/{len(video_files)})")
            
            cap = cv2.VideoCapture(video_file)
            if not cap.isOpened():
                print(f"❌ 파일을 열 수 없습니다: {video_file}")
                continue
            
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 프레임 크기가 다르면 리사이즈
                if frame.shape[1] != width or frame.shape[0] != height:
                    frame = cv2.resize(frame, (width, height))
                
                out.write(frame)
                current_frame += 1
                total_frames += 1
                
                # 진행률 표시
                if current_frame % 30 == 0:  # 30프레임마다 출력
                    progress = (current_frame / frame_count) * 100
                    print(f"  진행률: {progress:.1f}% ({current_frame}/{frame_count})")
            
            cap.release()
            print(f"✅ {video_file} 처리 완료 ({current_frame} 프레임)")
        
        out.release()
        print(f"✅ 성공적으로 합치기 완료: {output_file} (총 {total_frames} 프레임)")
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        return False

def find_mp4_files():
    """현재 폴더에서 mp4 파일 자동 찾기"""
    mp4_files = []
    for file in os.listdir('.'):
        if file.lower().endswith('.mp4'):
            mp4_files.append(file)
    return sorted(mp4_files)

if __name__ == "__main__":
    print("=== MP4 파일 합치기 도구 (OpenCV) ===")
    print(f"현재 작업 디렉토리: {os.getcwd()}")
    
    # 현재 폴더의 모든 mp4 파일 찾기
    available_mp4_files = find_mp4_files()
    
    if available_mp4_files:
        print(f"\n발견된 MP4 파일들:")
        for i, file in enumerate(available_mp4_files):
            file_size = os.path.getsize(file) / (1024*1024)  # MB
            print(f"  {i+1}. {file} (크기: {file_size:.2f} MB)")
        
        # 사용자가 직접 지정하거나 자동으로 모든 파일 사용
        print(f"\n모든 파일을 합치시겠습니까? (y/n)")
        choice = input().lower()
        
        if choice == 'y' or choice == '':
            video_files = available_mp4_files
        else:
            # 수동으로 파일 지정
            video_files = []
            print("합칠 파일 번호를 입력하세요 (예: 1,2,3):")
            try:
                indices = input().split(',')
                for idx in indices:
                    idx = int(idx.strip()) - 1
                    if 0 <= idx < len(available_mp4_files):
                        video_files.append(available_mp4_files[idx])
            except:
                print("잘못된 입력입니다. 모든 파일을 사용합니다.")
                video_files = available_mp4_files
    else:
        # 파일을 못 찾으면 기본값 사용
        print("MP4 파일을 찾을 수 없습니다. 기본 파일명을 사용합니다.")
        video_files = ["video1.mp4", "video2.mp4"]  # 원하는 파일명으로 변경
    
    # 출력 파일명
    output_mp4 = "merged_output2.mp4"
    
    # 파일 존재 확인
    print(f"\n합칠 파일 확인:")
    all_files_exist = True
    for video_file in video_files:
        if os.path.exists(video_file):
            file_size = os.path.getsize(video_file) / (1024*1024)  # MB
            print(f"✅ {video_file} (크기: {file_size:.2f} MB)")
        else:
            print(f"❌ {video_file} - 파일이 존재하지 않습니다")
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ 일부 파일이 존재하지 않습니다. 파일을 확인해주세요.")
        exit(1)
    
    # 합치기 실행
    print(f"\n{len(video_files)}개 파일을 {output_mp4}로 합치는 중...")
    success = merge_mp4_files(video_files, output_mp4)
    
    if success:
        print(f"\n🎉 완료! {output_mp4} 파일이 생성되었습니다.")
        if os.path.exists(output_mp4):
            output_size = os.path.getsize(output_mp4) / (1024*1024)  # MB
            print(f"출력 파일 크기: {output_size:.2f} MB")
    else:
        print(f"\n❌ 변환 실패!")