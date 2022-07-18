import os
from re import A
from xml.dom.minidom import parse,Element
from tqdm import tqdm


def txt_to_bboxinfo(txt_path):
    bbox_info = []
    f = open(txt_path, mode='r', encoding='utf-8')
    content = f.read()
    for info in content.split('\n'):
        info = info.split(' ')
        if len(info) == 1:
            continue
        label = info[0]
        xmin = int(info[1])
        ymin = int(info[2])
        xmax = int(info[3])
        ymax = int(info[4])
        bbox_info.append([label, xmin, ymin, xmax, ymax])
    return bbox_info


def get_bbox_txt(name, bbox_info, txt_save_dir):
    if os.path.exists(txt_save_dir)==0:
        os.makedirs(txt_save_dir)
    f = open('{}/{}.txt'.format(txt_save_dir, name), encoding='utf-8', mode='w')
    for object_info in bbox_info:
        for info in object_info:
            f.write(str(info))
            f.write(' ')
        f.write('\n')
    txt_path = '{}/{}.txt'.format(txt_save_dir, name)
    f.close()

    return txt_path


def readvocxml(xml_path, image_dir):
    """

    The function can read single xml file and transform information of xml file into a list containing:
    the filename of the xml indicates(str),
    the filepath of image that xml indicates(a str.you need to give the dir which this image located in.Aka,the second parameter.)
    the depth,height,width of the Image(three int data.channel first),
    the annotated objects' infomation.(
        a 2D int list:
        [
            row1:[label_1,xmin_1,ymin_1,xmax_1,ymax_1]
            row2:[label_2,xmin_2,ymin_2,xmax_2,ymax_2]
            ....
            row_i[label_i,xmin_i,ymin_i,xmax_i,ymax_i]
        ]
    )

    Args:

    xml_path:singal xml file's path.

    image_dir:the image's location dir that xml file indicates.


    """
    tree = parse(xml_path)
    rootnode = tree.documentElement
    sizenode = rootnode.getElementsByTagName('size')[0]
    width = int(sizenode.getElementsByTagName('width')[0].childNodes[0].data)
    height = int(sizenode.getElementsByTagName('height')[0].childNodes[0].data)
    depth = int(sizenode.getElementsByTagName('depth')[0].childNodes[0].data)

    name_node = rootnode.getElementsByTagName('filename')[0]
    filename = name_node.childNodes[0].data

    path = image_dir + '\\' + filename

    objects = rootnode.getElementsByTagName('object')
    objects_info = []
    for object in objects:
        label = object.getElementsByTagName('name')[0].childNodes[0].data
        xmin = int(object.getElementsByTagName('xmin')[0].childNodes[0].data)
        ymin = int(object.getElementsByTagName('ymin')[0].childNodes[0].data)
        xmax = int(object.getElementsByTagName('xmax')[0].childNodes[0].data)
        ymax = int(object.getElementsByTagName('ymax')[0].childNodes[0].data)
        info = []
        info.append(label)
        info.append(xmin)
        info.append(ymin)
        info.append(xmax)
        info.append(ymax)
        objects_info.append(info)

    return [filename, path, depth, height, width, objects_info]

def txt2classeslist(txt_path):
    with open(txt_path,'r') as f:
        content = f.read().split('\n')[:-1]
    return content


def getclasstxt(ann_dir,txt_path):
    classes_list = []
    for filename in tqdm(os.listdir(ann_dir)):
        path = ann_dir + '/' + filename
        _, _, _, _, _, objects_info = readvocxml(path,'')
        for object_ in objects_info:
            label = object_[0]
            if label in classes_list:
                continue
            else:
                classes_list.append(label)
    content = ''
    for class_ in classes_list:
        content = content + class_ + '\n'
    with open(txt_path,'w') as f:
        f.write(content)
    
    
    

getclasstxt(r'F:\VOCdevkit\VOC2007\Annotations',r'D:\PythonCode\OD_dataset_format\voc\classes.txt')