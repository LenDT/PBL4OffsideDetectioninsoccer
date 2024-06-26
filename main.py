from PoseEstimationUtils import *
from VanishingPointUtils import *
from TeamClassificationUtils import *
from CoreOffsideUtils import *
import demo.demo_multiperson as PoseGetter
from scipy.misc import imread, imsave
import matplotlib.pyplot as plt
from operator import itemgetter
import numpy as np
import math
import json
import sys
import os
import warnings
warnings.filterwarnings("ignore")

#Image folder path
base_path = './Offside_detection_dataset/Offside_Images/'
result_path = './Offside_detection_dataset/results/'
tempFileNames = os.listdir(base_path)
print(tempFileNames)
fileNames = []
for fileName in tempFileNames:
	fileNames.append(base_path+str(fileName))
	print(base_path+str(fileName))

#Output image paths
temp_viz_base_path = result_path+'sub/'
vanishing_point_viz_base_path = result_path+'vp/'
pose_estimation_viz_base_path = result_path+'pe/'
team_classification_viz_base_path = result_path+'tc/'
offside_viz_base_path = result_path+'final/'

#Direction of goal
goalDirection = 'right'

keeper = [4.4931905696916325e-06, 4.450801979411523e-06, 5.510516736414265e-07, 0.00021567314734519837, 0.002188183807439825, 0.0015186984125557716, 0.7527352297592997, 1.0, 0.20787746170678337]
referee = [8.72783130847647e-06, 1.5868784197229944e-07, 0.0, 0.0010298840944002235, 0.0002880184331797235, 0.002688172043010753, 0.3064516129032258, 0.05913978494623656, 1.0]


for file_itr in range(len(fileNames)):
	print('\n\n', fileNames[file_itr])
	print('in for loop')
	# calculate vanishing points
	imageForVanishingPoints = cv2.imread(fileNames[file_itr])
	vertical_vanishing_point = get_vertical_vanishing_point(imageForVanishingPoints, goalDirection)
	print(vertical_vanishing_point)
	horizontal_vanishing_point = get_horizontal_vanishing_point(imageForVanishingPoints)
	print(horizontal_vanishing_point)
	cv2.imwrite(vanishing_point_viz_base_path+tempFileNames[file_itr], imageForVanishingPoints)
	print('Finished Vanishing Point calculation')
	# get pose estimaitons and team classifications
	imageForPoseEstimation = cv2.imread(fileNames[file_itr])
	imageForPoseEstimation_2 = imread(fileNames[file_itr], mode='RGB')
	pose_estimations, isKeeperFound, isRefFound, temp_image = PoseGetter.return_pose(imageForPoseEstimation_2, imageForPoseEstimation, keeper, referee)
	print(pose_estimations)
	print(isKeeperFound)
	print(isRefFound)
	cv2.imwrite(temp_viz_base_path+tempFileNames[file_itr], temp_image)
	pose_estimations = sorted(pose_estimations, key=lambda x : x[-1][0])
	pose_estimations = update_pose_left_most_point(vertical_vanishing_point, horizontal_vanishing_point, pose_estimations, imageForPoseEstimation, goalDirection)
	print('Finished Pose Estimation & Team Classifiaciton')
	# pose_estimations structure -> [id, teamId, keyPoints, leftmostPoint]
	pose_estimations = get_leftmost_point_angles(vertical_vanishing_point, pose_estimations, imageForPoseEstimation, goalDirection)
	print('Finished updating leftmost point using angle')
	# pose_estimations structure -> [id, teamId, keyPoints, leftmostPoint, angleAtVanishingPoint]
	pose_estimations = sorted(pose_estimations, key=lambda x : x[-1])
	font = cv2.FONT_HERSHEY_SIMPLEX
	for pose in pose_estimations:
		cv2.putText(imageForPoseEstimation, str(str(pose[0])), (int(pose[-2][-1]), int(pose[-2][0])), font, 1, (200,255,155), 2, cv2.LINE_AA)
		cv2.line(imageForPoseEstimation, (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-2][-1]), int(pose[-2][0])), (0,255,0) , 2 )
	cv2.imwrite(pose_estimation_viz_base_path+tempFileNames[file_itr], imageForPoseEstimation)
	# visualize teams
	imageForTeams = cv2.imread(fileNames[file_itr])
	for pose in pose_estimations:
		font = cv2.FONT_HERSHEY_SIMPLEX
		cv2.putText(imageForTeams, str(pose[1]), (int(pose[-2][-1]), int(pose[-2][0])), font, 1, (200,255,155), 2, cv2.LINE_AA)
	cv2.imwrite(team_classification_viz_base_path+tempFileNames[file_itr], imageForTeams)
	print('cv in line 72')
	print(team_classification_viz_base_path+tempFileNames[file_itr])
	print(imageForTeams)
	# get offside decisions
	pose_estimations, last_defending_man = get_offside_decision(pose_estimations, vertical_vanishing_point, 0, 1, isKeeperFound)
	# pose_estimations structure -> [id, teamId, keyPoints, leftmostPoint, angleAtVanishingPoint, offsideDecision]
	print('Starting Core Offside Algorithm')
	imageForOffside = cv2.imread(fileNames[file_itr])
	for pose in pose_estimations:
		if pose[1] == 0:
			if pose[-1] == 'off':
				font = cv2.FONT_HERSHEY_SIMPLEX
				cv2.putText(imageForOffside, 'off', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
				cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
			else:
				font = cv2.FONT_HERSHEY_SIMPLEX
				cv2.putText(imageForOffside, 'on', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
		elif pose[1] == 1:
			if pose[0] == last_defending_man:
				cv2.putText(imageForOffside, 'last man', (int(pose[-3][-1]), int(pose[-3][0]-15)), font, 1, (200,255,155), 2, cv2.LINE_AA)
				cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
			else:
				cv2.putText(imageForOffside, 'def', (int(pose[-3][-1]), int(pose[-3][0]-15)), font, 1, (200,255,155), 2, cv2.LINE_AA)
				cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )				
		elif pose[1] == 2:
			cv2.putText(imageForOffside, 'keep', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
			cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
		elif pose[1] == 3:
			cv2.putText(imageForOffside, 'ref', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
			cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
	cv2.imwrite(offside_viz_base_path+tempFileNames[file_itr][:-4]+'_1.jpg', imageForOffside)
	print('cv in line 103')
	print(offside_viz_base_path+tempFileNames[file_itr][:-4]+'_1.jpg')
	print(imageForOffside)
	# exchange attacking and defending teams, get offside decisions
	pose_estimations, last_defending_man = get_offside_decision(pose_estimations, vertical_vanishing_point, 1, 0, isKeeperFound)
	# pose_estimations structure -> [id, teamId, keyPoints, leftmostPoint, angleAtVanishingPoint, offsideDecision]
	imageForOffside = cv2.imread(fileNames[file_itr])
	for pose in pose_estimations:
		if pose[1] == 1:
			if pose[-1] == 'off':
				font = cv2.FONT_HERSHEY_SIMPLEX
				cv2.putText(imageForOffside, 'off', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
				cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
			else:
				font = cv2.FONT_HERSHEY_SIMPLEX
				cv2.putText(imageForOffside, 'on', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
		elif pose[1] == 0:
			if pose[0] == last_defending_man:
				cv2.putText(imageForOffside, 'last man', (int(pose[-3][-1]), int(pose[-3][0]-15)), font, 1, (200,255,155), 2, cv2.LINE_AA)
				cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
			else:
				cv2.putText(imageForOffside, 'def', (int(pose[-3][-1]), int(pose[-3][0]-15)), font, 1, (200,255,155), 2, cv2.LINE_AA)
				cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
		elif pose[1] == 2:
			cv2.putText(imageForOffside, 'keep', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
			cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
		elif pose[1] == 3:
			cv2.putText(imageForOffside, 'ref', (int(pose[-3][-1]), int(pose[-3][0]-10)), font, 1, (200,255,155), 2, cv2.LINE_AA)
			cv2.line(imageForOffside , (int(vertical_vanishing_point[0]) , int(vertical_vanishing_point[1])) , (int(pose[-3][-1]), int(pose[-3][0])), (0,255,0) , 2 )
	cv2.imwrite(offside_viz_base_path+tempFileNames[file_itr][:-4]+'_2.jpg', imageForOffside)
	print('cv in line 133')
	print(offside_viz_base_path+tempFileNames[file_itr][:-4]+'_2.jpg')
	print(imageForOffside)
	print(file_itr,fileNames[file_itr])