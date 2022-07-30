import os
from xml.dom.minidom import parse, Document
from tqdm import tqdm
import json
import cv2


class Transformer(object):
    def __init__(self, src_dir: str,
                 xml_dir: str,
                 txt_dir: str,
                 json_path: str) -> None:
        super(Transformer, self).__init__()
        self.src_dir = src_dir
        self.xml_dir = xml_dir
        self.txt_dir = txt_dir
        self.json_path = json_path

    def readvocxml(self, xml_path, src_dir):
        tree = parse(xml_path)
        rootnode = tree.documentElement
        sizenode = rootnode.getElementsByTagName('size')[0]
        width = int(sizenode.getElementsByTagName('width')[0].childNodes[0].data)
        height = int(sizenode.getElementsByTagName('height')[0].childNodes[0].data)
        depth = int(sizenode.getElementsByTagName('depth')[0].childNodes[0].data)

        name_node = rootnode.getElementsByTagName('filename')[0]
        filename = name_node.childNodes[0].data

        path = os.path.join(src_dir, filename)
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

    def bbox2txt(self, objects_info, filename, save_dir):
        """
        Args:
            objects_info:
            a 2D int list:
                [
                    row1:[label_1,xmin_1,ymin_1,xmax_1,ymax_1]
                    row2:[label_2,xmin_2,ymin_2,xmax_2,ymax_2]
                    ....
                    row_i[label_i,xmin_i,ymin_i,xmax_i,ymax_i]
                ]
            filename:the txt filename.（txt前缀）
            save_dir:the directory you want to save txt file.
        """
        with open("{}/{}.txt".format(save_dir, filename), 'w') as f:
            lines = ""
            for object_ in objects_info:
                line = "{} {} {} {} {}\n".format(
                    object_[0],
                    object_[1],
                    object_[2],
                    object_[3],
                    object_[4]
                )
                lines = lines + line
            f.write(lines)

    def txt2bbox(self, txt_path):
        """
        Args:
            txt_path:单个txt路径
        Returns:
            objects_info:与txt存储方式一样的2D列表
            filename:文件名前缀
        """
        objects_info = []
        sig = 0  # 0:filename前是/,  1:filename前是\\
        for i in range(1, len(txt_path) + 1):
            if txt_path[-i] == '\\':
                sig = 1
                break
            if txt_path[-i] == '/':
                break
        if sig:
            filename = txt_path.split('\\')[-1].split('.')[0]
        else:
            filename = txt_path.split('/')[-1].split('.')[0]

        with open(txt_path, 'r') as f:
            info_list = f.read().split('\n')[:-1]
            info_list = [i.split() for i in info_list]

            for info in info_list:
                info_ = []
                info_.append(info[0])
                info_.append(int(info[1]))  # 位置信息: str->float
                info_.append(int(info[2]))
                info_.append(int(info[3]))
                info_.append(int(info[4]))
                objects_info.append(info_)
        return objects_info, filename

    def bbox2xml(self, objects_info, img_filename, image_shape, save_dir):
        """
        Args:
            objects_info:bbox列表
            img_filename:xml对应图片文件名
            image_shape:为了方便使用者自定义，需要手动输入
            classes_path:classes txt存储路径
            save_dir:xml保存目录
        """
        d, h, w = image_shape
        doc = Document()
        # 文件根节点
        annotation = doc.createElement('annotation')
        doc.appendChild(annotation)
        # 建立四个仅次于文件根节点的兄弟节点
        filename_node = doc.createElement('filename')
        annotation.appendChild(filename_node)
        filename_ = doc.createTextNode(img_filename)
        filename_node.appendChild(filename_)
        size_node = doc.createElement('size')
        annotation.appendChild(size_node)
        # size节点下分三个节点:width,height,depth
        w_node = doc.createElement('width')
        h_node = doc.createElement('height')
        d_node = doc.createElement('depth')
        size_node.appendChild(w_node)
        size_node.appendChild(h_node)
        size_node.appendChild(d_node)
        w_ = doc.createTextNode(str(w))
        h_ = doc.createTextNode(str(h))
        d_ = doc.createTextNode(str(d))
        w_node.appendChild(w_)
        h_node.appendChild(h_)
        d_node.appendChild(d_)

        for i in range(len(objects_info)):
            object_ = objects_info[i]
            name, xmin, ymin, xmax, ymax = object_
            object_node = doc.createElement('object')
            annotation.appendChild(object_node)
            # object下分两个节点：name和bndbox
            name_node = doc.createElement('name')
            object_node.appendChild(name_node)
            name_ = doc.createTextNode(name)
            name_node.appendChild(name_)
            # 位置信息结点建立
            bnd_node = doc.createElement('bndbox')
            object_node.appendChild(bnd_node)
            xmin_node = doc.createElement('xmin')
            ymin_node = doc.createElement('ymin')
            xmax_node = doc.createElement('xmax')
            ymax_node = doc.createElement('ymax')
            bnd_node.appendChild(xmin_node)
            bnd_node.appendChild(ymin_node)
            bnd_node.appendChild(xmax_node)
            bnd_node.appendChild(ymax_node)
            xmin_ = doc.createTextNode(str(xmin))
            ymin_ = doc.createTextNode(str(ymin))
            xmax_ = doc.createTextNode(str(xmax))
            ymax_ = doc.createTextNode(str(ymax))
            xmin_node.appendChild(xmin_)
            ymin_node.appendChild(ymin_)
            xmax_node.appendChild(xmax_)
            ymax_node.appendChild(ymax_)

        # 写入文件
        with open(save_dir + '/' + img_filename.split('.')[0] + '.xml', 'w') as f:
            f.write(doc.toprettyxml(indent="    "))

    def voc2txt(self):
        print("voc -> txt")
        for xml_name in tqdm(os.listdir(self.xml_dir)):
            xml_path = os.path.join(self.xml_dir, xml_name)
            filename, path, depth, height, width, objects_info = self.readvocxml(xml_path, self.src_dir)
            self.bbox2txt(objects_info,filename, self.txt_dir)
        print("Done.")

    def txt2voc(self):
        print("txt -> voc")
        for txt_name in tqdm(os.listdir(self.txt_dir)):
            txt_path = os.path.join(self.txt_dir, txt_name)
            objects_info, filename = self.txt2bbox(txt_path)
            # 默认为jpg格式  #########################################
            shape = cv2.imread(os.path.join(self.src_dir, "{}.jpg")).shape
            ########################################################
            self.bbox2xml(objects_info, filename, (shape[-1], shape[0], shape[1]), self.xml_dir)
        print("Done.")

    def voc2coco(self, txt_path):
        """
            Args:
                txt_path:classes.txt路径
        """
        print("voc -> coco")
        jpg_dir = self.src_dir
        ann_dir = self.xml_dir
        json_path = self.json_path
        obj = {'images': [], 'annotations': [], 'categories': []}
        # 先把种类搞定
        with open(txt_path, 'r') as f:
            cls_list = f.read().split('\n')[:-1]
        for i in range(len(cls_list)):
            cate_dict = {}
            cate_dict['id'] = i  # clslist下标作为cate_id
            cate_dict['name'] = cls_list[i]
            obj['categories'].append(cate_dict)
        # 搞定images和annotations
        for filename in tqdm(os.listdir(ann_dir)):
            img_dict = {}
            xml_path = ann_dir + '/' + filename
            filename, path, depth, height, width, objects_info = self.readvocxml(xml_path, jpg_dir)
            # img_dict
            img_dict['filename'] = filename
            img_dict['id'] = filename.split('.')[0]  # filename前缀作为id
            img_dict['depth'] = depth
            img_dict['height'] = height
            img_dict['width'] = width
            img_dict['path'] = path
            obj['images'].append(img_dict)
            # ann_duct
            for object_ in objects_info:
                ann_dict = {}
                ann_dict['bbox'] = object_[1:]
                ann_dict['category_id'] = object_[0]
                ann_dict['image_id'] = filename.split('.')[0]
                obj['annotations'].append(ann_dict)
        # 最后写入json文件
        with open(json_path, 'w') as fb:
            json.dump(obj, fb, indent="   ")
        print("Done.")

    def coco2voc(self, txt_path):
        """
            Args:txt_path:为voc生成的classes.txt路径
        """
        print("coco -> voc")
        src_dir = self.src_dir
        json_path = self.json_path
        ann_dir = self.xml_dir
        with open(json_path, 'r') as f:
            obj = json.load(f)
            ann_info = obj['annotations']
            cls_info = obj['categories']
            # 先生成classes.txt:
            id_cate = {}
            for item in cls_info:
                id_cate[int(item['id'])] = item['name']
            cls_list = [0 for i in range(len(id_cate))]
            for key in id_cate.keys():
                cls_list[key] = id_cate[key]  # 要保证id从小到大输出
            content = ""
            for cls in cls_list:
                content = content + cls + '\n'
            with open(txt_path, 'w') as f:
                f.write(content)
                # 建立图片-标注物体字典并完成转换
            img_obj_dict = {}
            for item in ann_info:
                img_obj_dict[item['image_id']] = []
            for item in ann_info:
                img_obj_dict[item['image_id']].append([item['category_id']] + item['bbox'])
            for key in tqdm(img_obj_dict.keys()):
            ######################  tips:默认图片格式为jpg，如果不是要改一下下方{}后的".jpg"  ######################
                img_path = src_dir + '/' + "{}.jpg".format(key)
                shape = cv2.imread(img_path).shape
                objects_info = img_obj_dict[key]
                self.bbox2xml(objects_info, key + '.jpg', (shape[-1], shape[0], shape[1]), ann_dir)
            ######################################################################################################
        print("Done.")