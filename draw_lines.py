from collections import deque
import numpy as np
import cv2

class DrawLines(object):
    def __init__(self, buffer_size=1):
        """For a video stream, increase the buffer size to keep state of
        previous frames, which helps to smooth out the detection of lane lines.
        """
        self.lft_avg = {'x1':deque(buffer_size*[np.nan], buffer_size),
                        'x2':deque(buffer_size*[np.nan], buffer_size),
                        'y1':deque(buffer_size*[np.nan], buffer_size),
                        'y2':deque(buffer_size*[np.nan], buffer_size)}
        self.rht_avg = {'x1':deque(buffer_size*[np.nan], buffer_size),
                        'x2':deque(buffer_size*[np.nan], buffer_size),
                        'y1':deque(buffer_size*[np.nan], buffer_size),
                        'y2':deque(buffer_size*[np.nan], buffer_size)}

    def __call__(self, image, return_all=False):
        """Processing pipeline.
        """
        blank = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
        vertices = np.array([[(0,              image.shape[0]),
                              (450,            325),
                              (520,            325),
                              (image.shape[1], image.shape[0])]],
                            dtype=np.int32)

        grayscale = self.grayscale(image)
        blurred = self.gaussian_blur(grayscale, 11)
        edges = self.canny(blurred, 40, 40*3)
        masked = self.region_of_interest(edges, vertices)
        hough_lines = self.hough_lines(masked, 1, np.pi/180, 15, 5, 5)
        lines = self.draw_lines(blank, hough_lines)
        weighted = self.weighted_image(lines, image)

        if return_all is not True:
            return weighted
        else:
            return [grayscale, blurred, edges, masked, lines, weighted]

    def draw_lines(self, image, lines, color=[255, 0, 0], thickness=3):
        """Take the average over all identified line segments in an image to
        draw out the full extent of each lane line.
        """
        lft = {'x1':[], 'x2':[], 'y1':[], 'y2':[]}
        rht = {'x1':[], 'x2':[], 'y1':[], 'y2':[]}

        for line in lines:
            for x1,y1,x2,y2 in line:
                angle = np.arctan2((y1-y2),(x1-x2))*180/np.pi
                if(np.absolute(angle) < 170 and np.absolute(angle) > 130):
                    slope = ((y2-y1)/(x2-x1))
                    if(slope < 0):
                        lft['x1'].append(x1)
                        lft['x2'].append(x2)
                        lft['y1'].append(y1)
                        lft['y2'].append(y2)
                    elif(slope > 0):
                        rht['x1'].append(x1)
                        rht['x2'].append(x2)
                        rht['y1'].append(y1)
                        rht['y2'].append(y2)

        for idx in ['x1','x2','y1','y2']:
            self.lft_avg[idx].append(np.mean(lft[idx]))
            self.rht_avg[idx].append(np.mean(rht[idx]))

        lft_params = np.polyfit([np.nanmean(self.lft_avg['x1'], axis=0),
                                 np.nanmean(self.lft_avg['x2'], axis=0)],
                                [np.nanmean(self.lft_avg['y1'], axis=0),
                                 np.nanmean(self.lft_avg['y2'], axis=0)], 1)
        rht_params = np.polyfit([np.nanmean(self.rht_avg['x1'], axis=0),
                                 np.nanmean(self.rht_avg['x2'], axis=0)],
                                [np.nanmean(self.rht_avg['y1'], axis=0),
                                 np.nanmean(self.rht_avg['y2'], axis=0)], 1)

        lft_poly = np.poly1d(lft_params)
        rht_poly = np.poly1d(rht_params)

        lft_pt1 = (0, int(lft_poly(0)))
        lft_pt2 = (450, int(lft_poly(450)))
        rht_pt1 = (520, int(rht_poly(520)))
        rht_pt2 = (image.shape[1], int(rht_poly(image.shape[1])))

        image = cv2.line(image, lft_pt1, lft_pt2, color, thickness)
        image = cv2.line(image, rht_pt1, rht_pt2, color, thickness)

        return image

    def hough_lines(self, image, rho, theta, threshold, min_line_len, max_line_gap):
        """Return an image with Hough lines drawn.
        NOTE: img must be the output of a Canny transform.
        """
        return cv2.HoughLinesP(image, rho, theta, threshold, np.array([]),
                               minLineLength=min_line_len, maxLineGap=max_line_gap)

    def grayscale(self, image):
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    def gaussian_blur(self, image, kernel_size):
        """Apply a Gaussian Noise kernel.
        """
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

    def canny(self, image, low_threshold, high_threshold):
        """Apply the Canny transform.
        """
        return cv2.Canny(image, low_threshold, high_threshold)

    def region_of_interest(self, image, vertices):
        """Set pixels outside the region of interest to black.
        """
        mask = np.zeros_like(image)

        if len(image.shape) > 2:
            channel_count = image.shape[2]  # i.e. 3 or 4 depending on your image
            ignore_mask_color = (255,) * channel_count
        else:
            ignore_mask_color = 255

        # filling pixels inside the polygon defined by "vertices"
        cv2.fillPoly(mask, vertices, ignore_mask_color)

        # returning the image only where mask pixels are nonzero
        return cv2.bitwise_and(image, mask)

    def weighted_image(self, img_a, img_b, α=0.8, β=1., λ=0.):
        """Return img_b overlayed on img_a.
        The result image is computed as follows: img_a * α + img_b * β + λ
        NOTE: initial_img and img must be the same shape
        """
        return cv2.addWeighted(img_a, α, img_b, β, λ)
