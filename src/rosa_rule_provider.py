import math
import os
import numpy as np
from src.pose_detector import PoseDetector
from matplotlib import pyplot as plt
import cv2


class RosaRuleProvider:
    def __init__(self, pose_detector):
        self.image = None
        self.pose_detector = pose_detector
        self.circle_radius = 3
        self.line_thickness = 2
        self.description = ""
        self.incorrect_pairs = []
        self.camera_view_point = "front"

    def get_posture_status(self, image, points, file_name, view_point, draw_joint_points=True):
        self.description = ""

        self.image = image
        self.camera_view_point = view_point
        posture_status = False
        chair_score = 1
        armrest_score = 1
        backrest_score = 1
        monitor_score = 1
        phone_score = 1
        mouse_score = 1

        if draw_joint_points:
            self.display_joint_points(points)

        print(f'ROSA score is checking for {file_name} ...\n')

        # Chair Height & Pan Depth (3/7)
        chair_score = self.get_chair_score(points)

        # Armrest (3/4)
        armrest_score = self.get_armrest_score(points)

        # Backrest (3/5)
        backrest_score = self.get_backrest_score(points)

        # Monitor (0/6)
        monitor_score = self.get_monitor_score(points)

        # Telephone (1/3)
        phone_score = self.get_phone_score(points)

        if chair_score > 1 or armrest_score > 1 or backrest_score > 1 or monitor_score > 1 or phone_score > 1:
            posture_status = False
        else:
            posture_status = True

        print(f'chair score is: {chair_score}\n'
              f'armrest score is: {armrest_score}\n'
              f'backrest score is: {backrest_score}\n'
              f'monitor score is: {monitor_score}\n'
              f'phone score is: {phone_score}\n'
              f'mouse score is: {mouse_score}\n')

        return posture_status

    def get_chair_score(self, points):
        chair_score = 1

        if self.camera_view_point == "side":
            r_hip_knee_ankle_angle = self.get_r_hip_knee_ankle_angle(points)
            l_hip_knee_ankle_angle = self.get_l_hip_knee_ankle_angle(points)
            r_hip_knee_ankle_points = [[self.pose_detector.RHip, self.pose_detector.RKnee],
                                       [self.pose_detector.RKnee, self.pose_detector.RAnkle]]
            l_hip_knee_ankle_points = [[self.pose_detector.LHip, self.pose_detector.LKnee],
                                       [self.pose_detector.LKnee, self.pose_detector.LAnkle]]

            if r_hip_knee_ankle_angle:
                if r_hip_knee_ankle_angle < 80:
                    chair_score = 2
                    self.draw_lines_between_pairs(points, r_hip_knee_ankle_points, False)
                    self.description = self.description + f'Chair is too low - right hip_knee_ankle angle: {r_hip_knee_ankle_angle}\n'
                elif r_hip_knee_ankle_angle > 100:
                    chair_score = 2
                    self.draw_lines_between_pairs(points, r_hip_knee_ankle_points, False)
                    self.description = self.description + f'Chair is too high - right hip_knee_ankle angle: {r_hip_knee_ankle_angle}\n'
                else:
                    self.draw_lines_between_pairs(points, r_hip_knee_ankle_points)
                    self.description = self.description + \
                                       f'Right knee status is in correct posture - right hip_knee_ankle angle: {r_hip_knee_ankle_angle}\n'

            if l_hip_knee_ankle_angle:
                if l_hip_knee_ankle_angle < 80:
                    chair_score = 2
                    self.draw_lines_between_pairs(points, l_hip_knee_ankle_points, False)
                    self.description = self.description + f'Chair is too low - left hip_knee_ankle angle: {l_hip_knee_ankle_angle}\n'
                elif l_hip_knee_ankle_angle > 100:
                    chair_score = 2
                    self.draw_lines_between_pairs(points, l_hip_knee_ankle_points, False)
                    self.description = self.description + f'Chair is too high - left hip_knee_ankle angle: {l_hip_knee_ankle_angle}\n'
                else:
                    self.draw_lines_between_pairs(points, l_hip_knee_ankle_points)
                    self.description = self.description + \
                                       f'Left knee status is in correct posture - left hip_knee_ankle angle: {l_hip_knee_ankle_angle}\n'
        return chair_score

    def get_armrest_score(self, points):
        armrest_score = 1

        if self.camera_view_point == "front":
            shoulders_neck_angle = self.get_shoulders_neck_angle(points)
            shoulders_neck_points = [[self.pose_detector.Neck, self.pose_detector.RShoulder],
                                     [self.pose_detector.Neck, self.pose_detector.LShoulder]]
            if shoulders_neck_angle:
                if shoulders_neck_angle < 160:
                    armrest_score = 2
                    self.draw_lines_between_pairs(points, shoulders_neck_points, False)
                    self.description = self.description + f'Shoulders are shrugged - shoulders_neck angle: {shoulders_neck_angle} \n'
                else:
                    self.draw_lines_between_pairs(points, shoulders_neck_points)
                    self.description = self.description + f'Shoulders are in normal posture - shoulders_neck angle: {shoulders_neck_angle} \n'

            r_shoulder_elbow_angle = None
            l_shoulder_elbow_angle = None

            if points[self.pose_detector.RShoulder] and points[self.pose_detector.RElbow]:
                r_shoulder_elbow_angle = self.get_angle_between_vector_and_vertical_axis(
                    np.array(points[self.pose_detector.RElbow]) - np.array(points[self.pose_detector.RShoulder]))

            if points[self.pose_detector.LShoulder] and points[self.pose_detector.LElbow]:
                l_shoulder_elbow_angle = self.get_angle_between_vector_and_vertical_axis(
                    np.array(points[self.pose_detector.LElbow]) - np.array(points[self.pose_detector.LShoulder]))

            if r_shoulder_elbow_angle:
                if r_shoulder_elbow_angle > 20:
                    armrest_score += 1
                    self.description = self.description + f'Right elbow is not inline with right shoulder - ' \
                                                          f'Angle between right shoulder_elbow and vertical axis: ' \
                                                          f'{r_shoulder_elbow_angle}\n'

            if l_shoulder_elbow_angle:
                if l_shoulder_elbow_angle > 20:
                    armrest_score += 1
                    self.description = self.description + f'Left elbow is not inline with left shoulder - ' \
                                                          f'Angle between left shoulder_elbow and vertical axis:' \
                                                          f' {l_shoulder_elbow_angle}\n'

            r_neck_shoulder_elbow = self.get_r_neck_shoulder_elbow_angle(points)
            r_neck_shoulder_elbow_points = [[self.pose_detector.Neck, self.pose_detector.RShoulder],
                                            [self.pose_detector.RShoulder, self.pose_detector.RElbow]]
            l_neck_shoulder_elbow = self.get_l_neck_shoulder_elbow_angle(points)
            l_neck_shoulder_elbow_points = [[self.pose_detector.Neck, self.pose_detector.LShoulder],
                                            [self.pose_detector.LShoulder, self.pose_detector.LElbow]]

            if r_neck_shoulder_elbow:
                if r_neck_shoulder_elbow > 120:
                    armrest_score += 1
                    self.draw_lines_between_pairs(points, r_neck_shoulder_elbow_points, False)
                    self.description = self.description + f'Too wide right elbow - ' \
                                                          f'right neck_shoulder_elbow angle: {r_neck_shoulder_elbow}\n'
                else:
                    self.draw_lines_between_pairs(points, r_neck_shoulder_elbow_points)
                    self.description = self.description + f'Right elbow is not too wide - ' \
                                                          f'right neck_shoulder_elbow angle: {r_neck_shoulder_elbow}\n'

            if l_neck_shoulder_elbow:
                if l_neck_shoulder_elbow > 120:
                    armrest_score += 1
                    self.draw_lines_between_pairs(points, l_neck_shoulder_elbow_points, False)
                    self.description = self.description + f'Too wide left elbow - ' \
                                                          f'left neck_shoulder_elbow angle: {l_neck_shoulder_elbow}\n'
                else:
                    self.draw_lines_between_pairs(points, l_neck_shoulder_elbow_points)
                    self.description = self.description + f'Left elbow is not too wide - ' \
                                                          f'left neck_shoulder_elbow angle: {l_neck_shoulder_elbow}\n'
        return armrest_score

    def get_backrest_score(self, points):
        backrest_score = 1

        if self.camera_view_point == "side":
            r_shoulder_hip_knee = self.get_r_shoulder_hip_knee_angle(points)
            r_shoulder_hip_knee_points = [[self.pose_detector.RShoulder, self.pose_detector.RHip],
                                          [self.pose_detector.RHip, self.pose_detector.RKnee]]
            l_shoulder_hip_knee = self.get_l_shoulder_hip_knee_angle(points)
            l_shoulder_hip_knee_points = [[self.pose_detector.LShoulder, self.pose_detector.LHip],
                                          [self.pose_detector.LHip, self.pose_detector.LKnee]]
            if r_shoulder_hip_knee:
                if r_shoulder_hip_knee < 95:
                    backrest_score = 2
                    self.draw_lines_between_pairs(points, r_shoulder_hip_knee_points, False)
                    self.description = self.description + f'Back rest is bent forward from right side - ' \
                                                          f'right shoulder_hip_knee angle: {r_shoulder_hip_knee}\n'
                elif r_shoulder_hip_knee > 110:
                    backrest_score = 2
                    self.draw_lines_between_pairs(points, r_shoulder_hip_knee_points, False)
                    self.description = self.description + f'Back rest is bent backward from right side - ' \
                                                          f'right shoulder_hip_knee angle: {r_shoulder_hip_knee}\n'
                else:
                    self.draw_lines_between_pairs(points, r_shoulder_hip_knee_points)
                    self.description = self.description + f'Back rest is normal from right side - ' \
                                                          f'right shoulder_hip_knee angle: {r_shoulder_hip_knee}\n'

            if l_shoulder_hip_knee:
                if l_shoulder_hip_knee < 95:
                    backrest_score = 2
                    self.draw_lines_between_pairs(points, l_shoulder_hip_knee_points, False)
                    self.description = self.description + f'Back rest is bent forward from left side - ' \
                                                          f'left shoulder_hip_knee angle: {l_shoulder_hip_knee}\n'
                elif l_shoulder_hip_knee > 110:
                    backrest_score = 2
                    self.draw_lines_between_pairs(points, l_shoulder_hip_knee_points, False)
                    self.description = self.description + f'Back rest is bent backward from left side - ' \
                                                          f'left shoulder_hip_knee angle: {l_shoulder_hip_knee}\n'
                else:
                    self.draw_lines_between_pairs(points, l_shoulder_hip_knee_points)
                    self.description = self.description + f'Back rest is normal from left side - ' \
                                                          f'left shoulder_hip_knee angle: {l_shoulder_hip_knee}\n'
        if self.camera_view_point == "front":
            shoulders_neck_angle = self.get_shoulders_neck_angle(points)
            if shoulders_neck_angle:
                if shoulders_neck_angle < 160:
                    backrest_score += 1
        return backrest_score

    def get_monitor_score(self, points):
        monitor_score = 1

        if self.camera_view_point == "side":
            r_hip_shoulder_ear_angle = self.get_r_hip_shoulder_ear_angle(points)
            r_hip_shoulder_ear_points = [[self.pose_detector.RHip, self.pose_detector.RShoulder],
                                         [self.pose_detector.RShoulder, self.pose_detector.REar]]
            l_hip_shoulder_ear_angle = self.get_l_hip_shoulder_ear_angle(points)
            l_hip_shoulder_ear_points = [[self.pose_detector.LHip, self.pose_detector.LShoulder],
                                         [self.pose_detector.LShoulder, self.pose_detector.LEar]]

            if r_hip_shoulder_ear_angle:
                if r_hip_shoulder_ear_angle < 140:
                    monitor_score += 1
                    self.draw_lines_between_pairs(points, r_hip_shoulder_ear_points, False)
                    self.description = self.description + f'Neck is bent forward from right side view - ' \
                                                          f'right hip_shoulder_ear angle: {r_hip_shoulder_ear_angle}\n'
                elif r_hip_shoulder_ear_angle > 200:
                    monitor_score += 3
                    self.draw_lines_between_pairs(points, r_hip_shoulder_ear_points, False)
                    self.description = self.description + f'Neck is bent backward from right side view - ' \
                                                          f'right hip_shoulder_ear angle: {r_hip_shoulder_ear_angle}\n'
                else:
                    self.draw_lines_between_pairs(points, r_hip_shoulder_ear_points)
                    self.description = self.description + f'Neck is normal from right side view - ' \
                                                          f'right hip_shoulder_ear angle: {r_hip_shoulder_ear_angle}\n'

            if l_hip_shoulder_ear_angle:
                if l_hip_shoulder_ear_angle < 140:
                    monitor_score += 1
                    self.draw_lines_between_pairs(points, l_hip_shoulder_ear_points, False)
                    self.description = self.description + f'Neck is bent forward from left side view - ' \
                                                          f'left hip_shoulder_ear angle: {l_hip_shoulder_ear_angle} \n'
                elif l_hip_shoulder_ear_angle > 200:
                    monitor_score += 3
                    self.draw_lines_between_pairs(points, l_hip_shoulder_ear_points, False)
                    self.description = self.description + f'Neck is bent backward from left side view - ' \
                                                          f'left hip_shoulder_ear angle: {l_hip_shoulder_ear_angle} \n'
                else:
                    self.draw_lines_between_pairs(points, l_hip_shoulder_ear_points)
                    self.description = self.description + f'Neck is normal from left side view - ' \
                                                          f'left hip_shoulder_ear angle: {l_hip_shoulder_ear_angle} \n'

            r_ear_eye_shoulder_angle = self.get_r_ear_eye_shoulder_angle(points)
            r_ear_eye_shoulder_points = [[self.pose_detector.REye, self.pose_detector.REar],
                                         [self.pose_detector.REar, self.pose_detector.RShoulder]]
            l_ear_eye_shoulder_angle = self.get_l_ear_eye_shoulder_angle(points)
            l_ear_eye_shoulder_points = [[self.pose_detector.LEye, self.pose_detector.LEar],
                                         [self.pose_detector.LEar, self.pose_detector.LShoulder]]
        if self.camera_view_point == "front":
            # neck rule front
            if points[self.pose_detector.LEye] and points[self.pose_detector.REye] and points[
                self.pose_detector.LShoulder] \
                    and points[self.pose_detector.RShoulder]:
                v1 = np.array(points[self.pose_detector.LEye]) - np.array(points[self.pose_detector.REye])
                v2 = np.array(points[self.pose_detector.LShoulder]) - np.array(points[self.pose_detector.RShoulder])
                angle_between_shoulders_and_eyes = self.get_angle_between_lines(v1, v2)

            # # neck rule twist side
            # neck_twisted_status_from_side = self.is_neck_twisted_from_side(points)

            # neck rule twist front
        return monitor_score

    def get_phone_score(self, points):
        phone_score = 1

        shoulders_distance = None
        wrists_distance = None

        if self.camera_view_point == "front":
            if points[self.pose_detector.RShoulder] and points[self.pose_detector.LShoulder]:
                shoulders_distance = self.calculate_distance_between_two_points(points[self.pose_detector.RShoulder],
                                                                                points[self.pose_detector.LShoulder])

            if points[self.pose_detector.RWrist] and points[self.pose_detector.LWrist]:
                wrists_distance = self.calculate_distance_between_two_points(points[self.pose_detector.RWrist],
                                                                             points[self.pose_detector.LWrist])

            r_neck_shoulder_elbow = self.get_r_neck_shoulder_elbow_angle(points)
            r_neck_shoulder_elbow_points = [[self.pose_detector.Neck, self.pose_detector.RShoulder],
                                            [self.pose_detector.RShoulder, self.pose_detector.RElbow]]
            l_neck_shoulder_elbow = self.get_l_neck_shoulder_elbow_angle(points)
            l_neck_shoulder_elbow_points = [[self.pose_detector.Neck, self.pose_detector.LShoulder],
                                            [self.pose_detector.LShoulder, self.pose_detector.LElbow]]

            if shoulders_distance and wrists_distance and r_neck_shoulder_elbow and l_neck_shoulder_elbow:
                if (math.fabs(wrists_distance - shoulders_distance) > shoulders_distance / 3) and \
                        math.fabs(r_neck_shoulder_elbow - l_neck_shoulder_elbow > 30):
                    phone_score = 2
                    self.description = self.description + 'Too wide wrists\n'

            if points[self.pose_detector.Neck] and points[self.pose_detector.Nose]:

                neck_nose_points = [[self.pose_detector.Neck, self.pose_detector.Nose]]
                neck_nose_angle = self.get_angle_between_vector_and_vertical_axis(
                    np.array(points[self.pose_detector.Neck]) - np.array(points[self.pose_detector.Nose]))
                if neck_nose_angle:
                    if neck_nose_angle > 30:
                        self.description = self.description + f'Neck is bent - ' \
                                                              f'angle between neck_nose and vertical axis: {neck_nose_angle}\n'
                        self.draw_lines_between_pairs(points, neck_nose_points, False)
                    else:
                        self.description = self.description + f'Neck is normal - ' \
                                                              f'angle between neck_nose and vertical axis: {neck_nose_angle}\n'
                        self.draw_lines_between_pairs(points, neck_nose_points)

        return phone_score

    def get_r_hip_knee_ankle_angle(self, points):
        # rHipKneeAnkle_pairs = [[8, 9], [9, 10]]
        angle = self.get_angle_between_points(points[self.pose_detector.RHip], points[self.pose_detector.RKnee],
                                              points[self.pose_detector.RAnkle])
        return angle

    def get_l_hip_knee_ankle_angle(self, points):
        # lHipKneeAnkle_pairs = [[11, 12], [12, 13]]
        angle = self.get_angle_between_points(points[self.pose_detector.LHip], points[self.pose_detector.LKnee],
                                              points[self.pose_detector.LAnkle])
        return angle

    def get_shoulders_neck_angle(self, points):
        # shoulders_neck_pairs = [[2, 1], [1, 5]]
        angle = self.get_angle_between_points(points[self.pose_detector.RShoulder], points[self.pose_detector.Neck],
                                              points[self.pose_detector.LShoulder])
        return angle

    def get_r_neck_shoulder_elbow_angle(self, points):
        # rNeckShoulderElbow_pairs = [[1, 2], [2, 3]]
        angle = self.get_angle_between_points(points[self.pose_detector.Neck], points[self.pose_detector.RShoulder],
                                              points[self.pose_detector.RElbow])
        return angle

    def get_l_neck_shoulder_elbow_angle(self, points):
        # lNeckShoulderElbow_pairs = [[1, 5], [5, 6]]
        angle = self.get_angle_between_points(points[self.pose_detector.Neck], points[self.pose_detector.LShoulder],
                                              points[self.pose_detector.LElbow])
        return angle

    def get_r_shoulder_hip_knee_angle(self, points):
        # rShoulderHipKnee_pairs = [[2, 8], [8, 9]]
        angle = self.get_angle_between_points(points[self.pose_detector.RShoulder], points[self.pose_detector.RHip],
                                              points[self.pose_detector.RKnee])
        return angle

    def get_l_shoulder_hip_knee_angle(self, points):
        # lShoulderHipKnee_pairs = [[5, 11], [11, 12]]
        angle = self.get_angle_between_points(points[self.pose_detector.LShoulder], points[self.pose_detector.LHip],
                                              points[self.pose_detector.LKnee])
        return angle

    def get_r_shoulder_elbow_wrist(self, points):
        # r_shoulder_elbow_wrist_pairs = [[2, 3], [3, 4]]
        angle = self.get_angle_between_points(points[self.pose_detector.RShoulder],
                                              points[self.pose_detector.RElbow], points[self.pose_detector.RWrist])
        return angle

    def get_l_shoulder_elbow_wrist(self, points):
        # l_shoulder_elbow_wrist_pairs = [[5, 6], [6, 7]]
        angle = self.get_angle_between_points(points[self.pose_detector.LShoulder],
                                              points[self.pose_detector.LElbow], points[self.pose_detector.LWrist])
        return angle

    def get_r_hip_shoulder_elbow_angle(self, points):
        # rHipShoulderElbow_pairs = [[3, 2], [2, 8]]
        angle = self.get_angle_between_points(points[self.pose_detector.RElbow],
                                              points[self.pose_detector.RShoulder], points[self.pose_detector.RHip])
        return angle

    def get_l_hip_shoulder_elbow_angle(self, points):
        # lHipShoulderElbow_pairs = [[6, 5], [5, 11]]
        angle = self.get_angle_between_points(points[self.pose_detector.LElbow],
                                              points[self.pose_detector.LShoulder], points[self.pose_detector.LHip])
        return angle

    def get_r_shoulder_elbow_wrist_angle(self, points):
        # rShoulderElbowWrist_pairs = [[2, 3], [3, 4]]
        angle = self.get_angle_between_points(points[self.pose_detector.RShoulder],
                                              points[self.pose_detector.RElbow], points[self.pose_detector.RWrist])
        return angle

    def get_l_shoulder_elbow_wrist_angle(self, points):
        # lShoulderElbowWrist_pairs = [[5, 6], [6, 7]]
        angle = self.get_angle_between_points(points[self.pose_detector.LShoulder],
                                              points[self.pose_detector.LElbow], points[self.pose_detector.LWrist])
        return angle

    def get_r_hip_shoulder_ear_angle(self, points):
        # r_hip_shoulder_ear_pairs = [[8, 2], [2, 16]]
        angle = self.get_angle_between_points(points[self.pose_detector.RHip],
                                              points[self.pose_detector.RShoulder], points[self.pose_detector.REar])
        return angle

    def get_l_hip_shoulder_ear_angle(self, points):
        # l_hip_shoulder_ear_pairs = [[11, 5], [5, 17]]
        angle = self.get_angle_between_points(points[self.pose_detector.LHip],
                                              points[self.pose_detector.LShoulder], points[self.pose_detector.LEar])
        return angle

    def get_r_ear_eye_shoulder_angle(self, points):
        # l_ear_eye_shoulder_pairs = [[16, 14], [14, 2]]
        angle = self.get_angle_between_points(points[self.pose_detector.REye],
                                              points[self.pose_detector.REar], points[self.pose_detector.RShoulder])
        return angle

    def get_l_ear_eye_shoulder_angle(self, points):
        # l_ear_eye_shoulder_pairs = [[17, 15], [15, 5]]
        angle = self.get_angle_between_points(points[self.pose_detector.LEye],
                                              points[self.pose_detector.LEar], points[self.pose_detector.LShoulder])
        return angle

    def get_angle_between_lines(self, v1, v2):
        len_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        len_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
        if len_v1 == 0 or len_v2 == 0:
            return None
        angle = math.acos(round(np.dot(v1, v2) / (len_v1 * len_v2), 5)) * 180 / math.pi
        if math.isnan(angle):
            return None
        return angle

    def calculate_distance_between_two_points(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def get_angle_between_vector_and_horizontal_axis(self, v1):
        v2 = np.array([1, 0])
        len_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        len_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
        if len_v1 == 0:
            return None
        return math.acos(round(np.dot(v1, v2) / (len_v1 * len_v2), 5)) * 180 / math.pi

    def get_angle_between_vector_and_vertical_axis(self, v1):
        v2 = np.array([0, 1])
        len_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        len_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
        if len_v1 == 0:
            return None
        return round(math.acos(round(np.dot(v1, v2) / (len_v1 * len_v2), 5)) * 180 / math.pi, 2)

    def get_vectors_between_points(self, p1, p2, p3, p4):
        v1 = np.array(p2) - np.array(p1)
        v2 = np.array(p4) - np.array(p3)
        return v1, v2

    def get_angle_between_points(self, p1, p2, p3):
        if p1 and p2 and p3:
            v1, v2 = self.get_vectors_between_points(p2, p1, p2, p3)
            angle = self.get_angle_between_lines(v1, v2)
            return round(angle, 2)
        else:
            return None

    def display_joint_points(self, points):
        for point in points:
            if point:
                cv2.circle(self.image, point, self.circle_radius, (0, 255, 0), thickness=-1, lineType=cv2.FILLED)

    def draw_lines_between_pairs(self, points, pairs, is_correct_edge=True):
        for pair in pairs:
            part_a = pair[0]
            part_b = pair[1]

            if points[part_a] and points[part_b]:
                if is_correct_edge and pair not in self.incorrect_pairs:
                    cv2.line(self.image, points[part_a], points[part_b], (0, 255, 255), self.line_thickness)
                else:
                    cv2.line(self.image, points[part_a], points[part_b], (0, 0, 255), self.line_thickness)
                    self.incorrect_pairs.append(pair)

    def save_image(self, is_correct_posture, output_directory, file_name):
        img_copy = self.image.copy()
        img = np.array(img_copy)[:, :, ::-1]
        plt.imshow(img)
        plt.axis('off')
        if is_correct_posture:
            plt.text(10, 30, 'Correct', color='yellow', fontsize=14)
            plt.savefig(f'{output_directory}/correct_posture/{file_name}')
        else:
            plt.text(10, 30, 'Incorrect', color='red', fontsize=14)
            plt.savefig(f'{output_directory}/incorrect_posture/{file_name}')
        plt.close()

        text_file = open(f'{output_directory}/log.txt', "a")
        text_file.write(f'Description of {file_name}:\n{self.description}'
                        f'f"*************************************************************************\n')
        text_file.close()
