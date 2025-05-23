import numpy as np
from time import sleep

from SCSCtrl import TTLServo
from Kinematics import Kinematic

class JBArm:
    def __init__(self):
        
        dh_params = np.array([
            (12, 78, np.deg2rad(90)),
            (94, 0, 0),
            (180, 0, 0),
        ])

        def in_workspace(x, dh_params):
            d1 = np.linalg.norm(x - np.array([0, 0, dh_params[0, 1]]))
            d2 = np.sum(dh_params[:, 0]) - 5
            return d1 < d2

        self.km = Kinematic(dh_params=dh_params, in_workspace=in_workspace)
        self.theta = None
        self.x = None
        
        self.ready_x, self.ready_theta = self.km.inverse(
            np.array([150, 0, 150]),
            np.deg2rad([0, -10, -20])
        )
        
        self.offsets = [7, -90, 90]
        
        self.release()
        self.ready()

    def move_theta(self, theta, speed=500):
        TTLServo.servoAngleCtrl(3, self.offsets[2] + theta[2], -1, speed)
        TTLServo.servoAngleCtrl(2, self.offsets[1] + theta[1], 1, speed)
        TTLServo.servoAngleCtrl(1, self.offsets[0] + theta[0], -1, speed)
        
        self.theta = theta
        self.x = self.km.forward(np.deg2rad(self.theta))

    def move_xyz(self, x_des, speed=500):
        theta = np.deg2rad([0, 10, -20])
        x, theta = self.km.inverse(x_des, theta)
        theta = np.rad2deg(theta)
        self.move_theta(theta, speed=speed)
        
    def move_to_xyz(self, x_des, speed=500):
        if self.x is None:
            self.move_xyz(x_des)
            return
        
        inc_x = (x_des - self.x)
        steps = int(np.linalg.norm(inc_x) / 10)
        dx = inc_x / steps
        
        for i in range(steps):
            self.move_xyz(self.x + dx)
            sleep(0.001)
            
    def ready(self):
        self.move_xyz(self.ready_x)
        sleep(2)
            
    def pick(self, x):
        # move top of target
        self.move_xyz(x + np.array([0, 0, 20]))
        sleep(2)
        
        # down
        self.move_xyz(x)
        sleep(2)
        
        # grab
        self.grab()
        
        # up
        self.move_xyz(x + np.array([0, 0, 100]))
        sleep(2)
        
        self.ready()
        
    def place(self, x):
        # move top of target
        self.move_xyz(x + np.array([0, 0, 50]))
        sleep(2)
        
        # down
        self.move_xyz(x)
        sleep(2)
        
        # release
        self.release()
        
        # up
        self.move_xyz(x + np.array([0, 0, 100]))
        sleep(2)
        
        self.ready()
    
    def grab(self):
        TTLServo.servoAngleCtrl(4, -20, 1, 500)
        sleep(2)
    
    def release(self):
        TTLServo.servoAngleCtrl(4, 10, 1, 500)
        sleep(2)
        
    
if __name__ == "__main__":
    # init jetbot arm, move to ready position
    arm = JBArm()
    sleep(2)

    # move along with X axis
    arm.move_to_xyz(arm.x + np.array([50, 0, 0]))
    sleep(2)

    # move along with Z axis
    arm.move_to_xyz(arm.x + np.array([0, 0, -230]))
    sleep(2)
    
    # to ready position
    arm.move_to_xyz(arm.ready_position)
    sleep(2)

    # move along with Y axis
    arm.move_to_xyz(np.array([150, -150, 150]))
    sleep(2)

    arm.move_to_xyz(arm.x + np.array([0, 300, 0]))
    sleep(2)

    # to ready position
    arm.move_to_xyz(arm.ready_position)
    sleep(2)

    # move along with X, Z plain
    arm.move_to_xyz(arm.x + np.array([50, 0, -230]))
    sleep(2)

    # grab
    arm.grab()
    sleep(2)
    
    # up
    arm.move_to_xyz(arm.x + np.array([-50, 0, 230]))
    sleep(2)
    
    # down
    arm.move_to_xyz(arm.x + np.array([50, 0, -230]))
    sleep(2)

    # release
    arm.release()
    sleep(2)

    # to ready position
    arm.move_to_xyz(arm.ready_position)
    sleep(2)