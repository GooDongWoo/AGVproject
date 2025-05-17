from tqdm import tqdm
import torch
import torch.optim as optim
import torch.nn.functional as F
import torchvision
import torchvision.datasets as datasets
import torchvision.models as models
from torchvision.models import ResNet18_Weights
import torchvision.transforms as transforms
import glob
import os
import numpy as np
import PIL
from PIL import Image, ImageFilter
import torchvision.transforms.functional as TF
import random
import multiprocessing  # Windows 멀티프로세싱 지원을 위해 추가

# 상수 정의
DATASET_DIR = 'data'  # 데이터셋 경로
BATCH_SIZE = 512  # 배치 크기

def get_x(path):
    """Gets the x value from the image filename"""
    return (float(int(path[3:6])) - 50.0) / 50.0  # 이미지 이름에서 x 좌표 추출 및 정규화

def get_y(path):
    """Gets the y value from the image filename"""
    return (float(int(path[7:10])) - 50.0) / 50.0  # 이미지 이름에서 y 좌표 추출 및 정규화


class XYDataset(torch.utils.data.Dataset):
    def __init__(self, directory, transform=True):
        self.directory = directory  # 데이터 디렉토리 경로
        self.transform = transform  # 증강 적용 여부
        self.image_paths = glob.glob(os.path.join(self.directory, '*.jpg'))  # 모든 jpg 파일 경로 수집
        
        # 색상 변형을 위한 ColorJitter 정의
        self.color_jitter = transforms.ColorJitter(
            brightness=0.3,  # 밝기 변화 범위 
            contrast=0.3,    # 대비 변화 범위
            saturation=0.3,  # 채도 변화 범위
            hue=0.1          # 색조 변화 범위
        )
        
    def __len__(self):
        return len(self.image_paths)  # 데이터셋 크기 반환
    
    def apply_augmentations(self, image, x, y):
        orig_w, orig_h = image.size  # 원본 이미지 크기 저장
        
        if random.random() < 0.8:  # 80% 확률로 색상 지터링 적용
            image = self.color_jitter(image)
        
        if random.random() < 0.3:  # 30% 확률로 색상 반전 적용
            image = TF.invert(image)
        
        if random.random() < 0.3:  # 30% 확률로 가우시안 블러 적용
            blur_radius = random.uniform(0.5, 1.5)
            image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        if random.random() < 0.3:  # 30% 확률로 추가 밝기 조정
            brightness_factor = random.uniform(0.8, 1.2)
            image = TF.adjust_brightness(image, brightness_factor)
        
        if random.random() < 0.3:  # 30% 확률로 추가 대비 조정
            contrast_factor = random.uniform(0.8, 1.2)
            image = TF.adjust_contrast(image, contrast_factor)
            
        if random.random() < 0.3:  # 30% 확률로 채도 조정
            saturation_factor = random.uniform(0.8, 1.2)
            image = TF.adjust_saturation(image, saturation_factor)
        
        if random.random() < 0.2:  # 20% 확률로 가우시안 노이즈 적용
            image_np = np.array(image).astype(np.float32)
            noise = np.random.normal(0, 5, image_np.shape)  # 평균 0, 표준편차 5의 노이즈
            image_np = np.clip(image_np + noise, 0, 255).astype(np.uint8)
            image = Image.fromarray(image_np)
            
        return image, x, y  # 증강된 이미지와 좌표 반환
    
    def __getitem__(self, idx):
        image_path = self.image_paths[idx]  # 인덱스에 해당하는 이미지 경로
        
        image = PIL.Image.open(image_path).convert('RGB')  # RGB 이미지로 불러오기
        
        # 파일 이름에서 좌표 추출
        x = float(get_x(os.path.basename(image_path)))  # x 좌표 추출
        y = float(get_y(os.path.basename(image_path)))  # y 좌표 추출
        
        if self.transform:  # 증강 적용 여부 확인
            image, x, y = self.apply_augmentations(image, x, y)  # 증강 적용
        
        orig_w, orig_h = image.size  # 현재 이미지 크기 저장
        
        image = transforms.functional.resize(image, (224, 224))  # 224x224로 크기 조정
        
        # 좌표 스케일 조정
        x = x * (224 / orig_w)  # x 좌표 스케일 조정
        y = y * (224 / orig_h)  # y 좌표 스케일 조정
        
        image = transforms.functional.to_tensor(image)  # 이미지를 텐서로 변환
        
        # RGB -> BGR 변환 및 복사
        image = image.numpy()[::-1].copy()  # 채널 순서 반전
        image = torch.from_numpy(image)  # 다시 텐서로 변환
        
        # ImageNet 평균/표준편차로 정규화
        image = transforms.functional.normalize(image, 
                                              [0.485, 0.456, 0.406], 
                                              [0.229, 0.224, 0.225])
        
        return image, torch.tensor([x, y]).float()  # 이미지와 좌표 텐서 반환


# 모든 실행 코드를 if __name__ == '__main__': 블록 안으로 이동
if __name__ == '__main__':
    # Windows 멀티프로세싱을 위한 필수 호출
    multiprocessing.freeze_support()
    
    # 데이터셋 생성
    dataset = XYDataset(DATASET_DIR)
    
    # 데이터셋 분할
    test_percent = 0.1  # 테스트 데이터 비율
    num_test = int(test_percent * len(dataset))  # 테스트 데이터 개수
    train_dataset, test_dataset = torch.utils.data.random_split(dataset, [len(dataset) - num_test, num_test])  # 학습/테스트 분할

    # 데이터로더 생성
    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,  # 학습 데이터 섞기
        num_workers=1  # 병렬 처리 작업자 수
    )

    test_loader = torch.utils.data.DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=1
    )

    # 모델 정의
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)  # 사전학습된 ResNet18 모델 로드
    model.fc = torch.nn.Linear(512, 2)  # 출력층을 x,y 좌표(2개) 예측용으로 변경
    device = torch.device('cuda')  # GPU 사용
    model = model.to(device)  # 모델을 GPU로 이동

    # 학습 설정
    NUM_EPOCHS = 500  # 학습 에폭 수
    BEST_MODEL_PATH = 'best.pth'  # 최적 모델 저장 경로
    best_loss = 1e9  # 최적 손실값 초기화

    optimizer = optim.Adam(model.parameters())  # Adam 옵티마이저 사용

    # 에폭 반복 (tqdm으로 진행률 표시)
    for epoch in tqdm(range(NUM_EPOCHS), desc="Epochs"):
        
        # 학습 단계
        model.train()  # 모델을 학습 모드로 설정
        train_loss = 0.0  # 학습 손실값 초기화
        for images, labels in tqdm(train_loader, desc=f"Train Epoch {epoch+1}/{NUM_EPOCHS}", leave=False):
            images = images.to(device)  # 이미지를 GPU로 이동
            labels = labels.to(device)  # 라벨을 GPU로 이동
            optimizer.zero_grad()  # 그래디언트 초기화
            outputs = model(images)  # 모델 예측
            loss = F.mse_loss(outputs, labels)  # MSE 손실 계산
            train_loss += float(loss)  # 손실값 누적
            loss.backward()  # 역전파
            optimizer.step()  # 모델 파라미터 업데이트
        train_loss /= len(train_loader)  # 평균 학습 손실 계산
        
        # 평가 단계
        model.eval()  # 모델을 평가 모드로 설정
        test_loss = 0.0  # 테스트 손실값 초기화
        for images, labels in tqdm(test_loader, desc=f"Test Epoch {epoch+1}/{NUM_EPOCHS}", leave=False):
            images = images.to(device)  # 이미지를 GPU로 이동
            labels = labels.to(device)  # 라벨을 GPU로 이동
            outputs = model(images)  # 모델 예측
            loss = F.mse_loss(outputs, labels)  # MSE 손실 계산
            test_loss += float(loss)  # 손실값 누적
        test_loss /= len(test_loader)  # 평균 테스트 손실 계산
        
        # 결과 출력 및 모델 저장
        print(f'Epoch {epoch+1}/{NUM_EPOCHS} - Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}')
        if test_loss < best_loss:  # 현재 테스트 손실이 최적값보다 작으면
            torch.save(model.state_dict(), BEST_MODEL_PATH)  # 모델 저장
            best_loss = test_loss  # 최적 손실값 갱신

    print('success')  # 학습 완료 메시지