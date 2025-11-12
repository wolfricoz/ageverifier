# import easyocr
# import cv2
#
# reader = easyocr.Reader(['nl'])  # or ['nl'] for Dutch
# result = reader.readtext('id_scanner.jpg')
#
# for (bbox, text, confidence) in result:
#     print(f"{text} (confidence: {confidence})")


import easyocr
import cv2

from parsers.NL.ID import IDParser

FILE = 'id_scanner.jpg'
PARSED_FILE = 'ID_PARSED.jpg'
files = ['id_scanner.jpg', 'id_test.jpg', 'test1.jpg', 'test2.jpg']








for file in files :

	parser = IDParser()

	print("===VERIFYING " + file + "===")
	image = cv2.imread(file)
	img = cv2.imread(file)

	# Grayscale
	gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	# Initialize reader
	reader = easyocr.Reader(['nl', 'en'], gpu=False)

	# Read full image
	print("===Regular Image (with beam)===")
	results = reader.readtext(gray_img,
	                          decoder='beamsearch',
	                          )
	dob = parser.extract_dob(results)
	print(f"{file}: {dob}")
	# for (bbox, text, prob) in results :
	# 	print(f"Text: {text}, Probability: {prob}")
	# dob = extract_dob(results)
	# print(f"{file}: {dob}")
	# print("===Gray Image===")
	# results = reader.readtext(gray_img)
	#
	# for (bbox, text, prob) in results :
	# 	print(f"Text: {text}, Probability: {prob} ")
	# dob = extract_dob(results)
	# print(f"{file}: {dob}")
	# blur = cv2.resize(gray_img, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)
	#
	# print("===Gray with blur removed Image===")
	# results = reader.readtext(blur)
	# dob = extract_dob(results)
	# print(f"{file}: {dob}")
	# for (bbox, text, prob) in results :
	# 	print(f"Text: {text}, Probability: {prob} ")
