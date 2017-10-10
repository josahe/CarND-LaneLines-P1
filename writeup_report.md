# **Finding Lane Lines on the Road** 

---

The goals / steps of this project were the following:
* Make a pipeline that finds lane lines on the road
* Reflect on the work in a written report
  * Describe the pipeline and how the draw_lines() function was modified
  * Identify potential shortcomings with your current pipeline
  * Suggest possible improvements to your pipeline

[//]: # (Image References)

[image0]: ./test_images_output/0_original.jpg "Original"
[image1]: ./test_images_output/0_grayscale.jpg "Grayscale"
[image2]: ./test_images_output/0_gaussian.jpg "Gaussian"
[image3]: ./test_images_output/0_cannyedge.jpg "CannyEdge"
[image4]: ./test_images_output/0_masked.jpg "Masked"
[image5]: ./test_images_output/0_houghlines.jpg "Hough"
[image6]: ./test_images_output/0_overlayed.jpg "Overlayed"

![alt text][image0]

---

## Reflection

My pipeline consists of 6 steps.

### Step 1
The frame is converted to grayscale.
![alt text][image1]

### Step 2
The image is blurred to reduce any image noise that could result in unwanted edges.
![alt text][image2]

### Step 3
The Canny edge detection algorithm is applied to the image.
![alt text][image3]

### Step 4
The image is masked to leave only the edge-detected lane lines.
![alt text][image4]

### Step 5
A Hough transform is used to detect lines in the masked image, and the detected lines are drawn in red.
![alt text][image5]

#### The DrawLines class
The original draw_lines() function simply used the (x1,y1) and (x2,y2) points provided by the HoughLinesP() function, to draw all the detected lines directly on to the image. In order to draw a single line on each of the left and right lanes, the draw_lines() function was first modified to differentiate between lanes on the left (negative slope) and lanes on the right (positive slope). Then, the left and right averages of all the (x1,y1) and (x2,y2) points within a frame are fed into a polynomial fitting algorithm. The computed parameters of the equation of a straight line can then be used to draw out a single line from the bottom of the image up to a suitable distance - about halfway up the image. This modification was suitable enough for the still images. In order to smooth out the drawing of single lines on each of the left and right lanes for a moving image, the draw_lines() function was swapped for a callable class, DrawLines. A class implementation allows state saving between image frames, and for a second stage of averaging across multiple frames. Any spurious horizontal/vertical lines detected are ignored.

### Step 6
Finally, the detected lines are overlayed on the original image.
![alt text][image6]

## Shortcomings with the current pipeline

1. The masking stage is quite rudimentary as it blindly ignores data outside a static region of interest. As can be seen in the third, challenging test video, the region of interest may move in the image
2. Old, faded lane lines could confuse the algorithm
3. An overtaking car that veers into the lane infront may cause outliers to affect the running average and the overlayed lines will deviate from the lane lines

## Possible improvements to the current pipeline

1. Make the region of interest dynamically calculated - possibly by using data from additional sensors to determine where on the highway the car is
2. If a second, faded lane line is detected, a voting algorithm could determine which is the more likely correct lane line
