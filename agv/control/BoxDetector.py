import cv2
import numpy as np

class BoxDetector:
    def __init__(self):
        
        # camera parameter
        self.cam_intrinsic = np.array([
            [146.7755, 0, 151.9934],
            [0, 196.3291, 134.7969],
            [0, 0, 1]
        ], dtype=np.float32)
        self.cam_dist = np.array([-0.2865, 0.0591, 0.0, 0.0, 0.0], dtype=np.float32)
        
        # marker info
        self.marker_sz = 30
        s = self.marker_sz / 2
        self.marker_3d_edges = np.array([
            [-s,  s, 0],   # 좌상
            [ s,  s, 0],   # 우상
            [ s, -s, 0],   # 우하
            [-s, -s, 0]    # 좌하
        ], dtype=np.float32)
        
        # ArUco 딕셔너리
        arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(arucoDict, parameters)
        
        # frame transform
        T1 = self.transform_3d(0, 0, 0, 41, 0, 27)
        T2 = self.transform_3d(0, 30, 0, 53, 0, 0)
        T3 = self.transform_3d(-90, 90, 0, 0, 0, 0)
        self.A = T1 @ T2 @ T3
        
        self.off_r = 15
        self.off_z = -(35 / 2)
        
    def detect_boxes(self, frame):
        corners, ids, rejected = self.detector.detectMarkers(frame)
        ret = {}

        if ids is not None:
            for i, corner in enumerate(corners):
                corner = corner.reshape((4, 2))
                success, rvec, tvec = cv2.solvePnP(self.marker_3d_edges, corner, self.cam_intrinsic, self.cam_dist)

                if success:
                    R, _        = cv2.Rodrigues(rvec)
                    cam_corners = (R @ self.marker_3d_edges.T).T + tvec.T
                    center      = cam_corners.mean(axis=0)
                    
                    x_world = self.A @ np.hstack([center, [1]])
                    
                    target_theta = np.arctan2(x_world[1], x_world[0])
                    off_x = np.cos(target_theta) * self.off_r
                    off_y = np.sin(target_theta) * self.off_r

                    ret[int(ids[i][0])] = x_world[:3] + np.array([off_x, off_y, self.off_z])

        return ret
        
    @staticmethod
    def transform_3d(roll, pitch, yaw, dx, dy, dz):
        roll, pitch, yaw = map(np.deg2rad, (roll, pitch, yaw))

        Rx = np.array([
            [1, 0, 0, 0],
            [0, np.cos(roll), -np.sin(roll), 0],
            [0, np.sin(roll), np.cos(roll), 0],
            [0, 0, 0, 1]
        ])

        Ry = np.array([
            [np.cos(pitch), 0, np.sin(pitch), 0],
            [0, 1, 0, 0],
            [-np.sin(pitch), 0, np.cos(pitch), 0],
            [0, 0, 0, 1]
        ])

        Rz = np.array([
            [np.cos(yaw), -np.sin(yaw), 0, 0],
            [np.sin(yaw), np.cos(yaw), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ])

        R = Rx @ Ry @ Rz
        R[:, 3] = np.array([dx, dy, dz, 1])

        return R