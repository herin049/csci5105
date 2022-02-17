import cv2

if __name__ == '__main__':
    img = cv2.imread('test.png')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(image=gray, threshold1=100, threshold2=200)
    cv2.imwrite(filename='test_out.png', img=edges)
