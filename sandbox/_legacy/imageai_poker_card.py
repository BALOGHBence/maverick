from imageai.Detection import ObjectDetection

detector = ObjectDetection()

model_path = "E:\\yolo-tiny.h5"
input_path = "E:\\cars.png"
output_path = "E:\\cars_.png"

detector.setModelTypeAsTinyYOLOv3()
detector.setModelPath(model_path)
detector.loadModel()
detection = detector.detectObjectsFromImage(input_image=input_path,
                                            output_image_path=output_path)

for eachItem in detection:
    print(eachItem["name"] , " : ", eachItem["percentage_probability"])
