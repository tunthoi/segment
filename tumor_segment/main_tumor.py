from model_tumor import LstmSegNet
from get_data import *
import re
from tools import *
from train_tumor import net_train
from val_tumor import net_val
import argparse
from statistics import *


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


parser = argparse.ArgumentParser(
    description='tumor segmentation with lstmConvNet by tensorflow')

parser.add_argument('--dataset_root', default="/workspace/mnt/group/alg-pro/yankai/segment/data/pre_process_tumor",
                    help='Dataset root directory path')

parser.add_argument('--save_path', default="tumor_segment",
                    help='the path tensorboard and model save at')

parser.add_argument('--batch_size', default=12, type=int,
                    help='Batch size for training')

parser.add_argument('--resume', default=True, type=str,
                    help='Checkpoint state_dict file to resume training from')

parser.add_argument('--cuda', default=True, type=str2bool,
                    help='Use CUDA to train model')

parser.add_argument('--lr', '--learning-rate', default=0.1, type=float,
                    help='initial learning rate')

parser.add_argument('--decay_rate', default=0.99, type=float,
                    help='rate of weight decay for learning_rate')

parser.add_argument('--decay_steps', default=300, type=int,
                    help='Weight decay steps for SGD')

parser.add_argument('--threshold', default=0.5, type=float,
                    help='threshold to filter probability map of tumor')

parser.add_argument('--width', default=512, type=int,
                    help='the width of input data')

parser.add_argument('--height', default=512, type=int,
                    help='the height of input data')

parser.add_argument('--epochs', default=200, type=int,
                    help='the number of epochs for training')

parser.add_argument('--loss_func', default='cross_entropy', type=str,
                    help='loss_func for training')

parser.add_argument('--weights', default=[100, 1], type=list,
                    help='the weights of proportion between object and background')

parser.add_argument('--filter_no_tumor', default=10, type=int,
                    help='the probability to filter on_object')

parser.add_argument('--down_sample', default=1, type=int,
                    help='the probability to filter on_object')

parser.add_argument('--norm_type', default='batch', type=str,
                    help='the type of normlization')

parser.add_argument('--supervise', default=True, type=bool,
                    help='the type of normlization')

args = parser.parse_args()

args.width = args.width // args.down_sample

args.height = args.height // args.down_sample

if __name__ == '__main__':

    layers = [
        'RES_1', 'RES_2', 'RES_3', 'RES_4', 'RES_5', 'ATROUS', 'LSTM', 'UPSAMPLE_1', 'CONBINE_1', 'RES_8',
        'UPSAMPLE_2', 'CONBINE_2', 'RES_9', 'UPSAMPLE_3', 'CONBINE_3', 'RES_10', 'UPSAMPLE_5', 'CONBINE_5',
        'RES_11', 'CONV_LAST'
    ]
    layers_kernels = [
        {"num": 1, "filter": 32, "stride": 1, "norm": args.norm_type, "supervise": False},  # RES_1
        {"num": 1, "filter": 64, "stride": 2, "norm": args.norm_type, "supervise": args.supervise},  # RES_2
        {"num": 1, "filter": 128, "stride": 2, "norm": args.norm_type, "supervise": False},  # RES_3
        {"num": 1, "filter": 256, "stride": 2, "norm": args.norm_type, "supervise": args.supervise},  # RES_4
        {"num": 1, "filter": 512, "stride": 2, "norm": args.norm_type, "supervise": False},  # RES_5

        {"filter": 512},

        {"filter": 512, "norm": args.norm_type},

        {"kernel": [3, 3], "stride": [2, 2], "filter": 256},  # UPSAMPLE_3
        {"add_layer": 'RES_4', "kernel": [1, 1]},  # CONBINE_3
        {"num": 1, "filter": 256, "stride": 1, "norm": args.norm_type, "supervise": False},  # RES_9

        {"kernel": [3, 3], "stride": [2, 2], "filter": 128},  # UPSAMPLE_4
        {"add_layer": 'RES_3', "kernel": [1, 1]},  # CONBINE_4
        {"num": 1, "filter": 128, "stride": 1, "norm": args.norm_type, "supervise": False},  # RES_10

        {"kernel": [3, 3], "stride": [2, 2], "filter": 64},  # UPSAMPLE_5
        {"add_layer": 'RES_2', "kernel": [1, 1]},  # CONBINE_5
        {"num": 1, "filter": 64, "stride": 1, "norm": args.norm_type, "supervise": False},  # RES_11

        {"kernel": [3, 3], "stride": [2, 2], "filter": 32},  # UPSAMPLE_5
        {"add_layer": 'RES_1', "kernel": [1, 1]},  # CONBINE_5
        {"num": 1, "filter": 32, "stride": 1, "norm": args.norm_type, "supervise": False},  # RES_11

        {"kernel": [3, 3], "stride": 1, "filter": 2, "norm": args.norm_type}  # CONV_LAST
    ]

    model = LstmSegNet(layers=layers, layers_kernels=layers_kernels,
                       threshold=args.threshold, save_path=args.save_path, learning_rate=args.lr,
                       decay_steps=args.decay_steps, decay_rate=args.decay_rate, batch_size=args.batch_size,
                       width=args.width, height=args.height, resume=args.resume, loss_func=args.loss_func
                       )
    file_list = [file for file in os.listdir(args.dataset_root) if
                 int(re.sub("\D", "", file)) <= 110 and "volume" in file]
    file_test_list = [file for file in os.listdir(args.dataset_root) if
                      int(re.sub("\D", "", file)) > 110 and "volume" in file]

    avg_tumor_best = [0 for i in range(len(file_test_list))]

    model.train_times = 0
    model.test_times = 0

    weights = args.weights
    init_statistics(save_path=args.save_path, batch_size=args.batch_size, learning_rate=args.lr,
                    decay_rate=args.decay_rate,
                    decay_steps=args.decay_steps, threshold=args.threshold, width=args.width, height=args.height,
                    loss_func=args.loss_func, weights=args.weights, filter_no_tumor=args.filter_no_tumor
                    )
    count = 5
    for time in range(args.epochs):
        net_train(model=model, root=args.dataset_root, weights=weights, times=time + 1, down_sample=args.down_sample)
        avg_tumor = net_val(model=model, root=args.dataset_root, weights=weights, times=time + 1,
                            down_sample=args.down_sample)

        if (np.sum(avg_tumor) > np.sum(avg_tumor_best)):
            avg_tumor_best = avg_tumor
            model._store(True)
        else:
            model._store(False)
        print("avg_tumor_best: " + str(np.sum(avg_tumor_best) / len(file_test_list)))

        if weights[1] + 5 < 100:
            weights[1] += 5
        else:
            weights[1] = 5
