import torch
import numpy as np
import random
import argparse
import os
import time
import warnings

warnings.simplefilter("ignore")

# ensure result consistency
seed = 42
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
np.random.seed(seed)
random.seed(seed)

from algo.server.Real import Server as Real
from algo.server.Gen import Server as Gen
from algo.server.GenLLM import Server as GenLLM
from algo.server.Img2Cap import Server as Img2Cap
from algo.server.Filter import Server as Filter
from algo.server.Feedback import Server as Feedback


def run(args):
    start = time.time()
    timestamp = args.timestamp if args.timestamp else str(time.time())
    print('Start timestamp:', timestamp)
    i2i_strength = args.i2i_strength
    for i in range(args.times):
        print(f"\n============= Running time: {i}th =============")
        print("Initiating ...")
        args.i2i_strength = i2i_strength
        args.task = os.path.join(
            args.task_mode, 
            args.server_generator, 
            args.rater, 
            args.client_dataset, 
            timestamp, 
            str(i)
        )

        if args.framework == 'Real':
            server = Real(args)

        elif args.framework == 'Gen':
            server = Gen(args)

        elif args.framework == 'GenLLM':
            server = GenLLM(args)

        elif args.framework == 'Img2Cap':
            server = Img2Cap(args)

        elif args.framework == 'Filter':
            server = Filter(args)

        elif args.framework == 'Feedback':
            server = Feedback(args)

        else:
            raise NotImplementedError
                
        server.run()
        torch.cuda.empty_cache()

    print(f"\nTotal time cost: {round(time.time()-start, 2)}s.")
    print("All done!")


if __name__ == "__main__":
    total_start = time.time()

    parser = argparse.ArgumentParser()
    # general
    parser.add_argument('-ts', "--timestamp", type=str, default="")
    parser.add_argument('-tt', "--task_type", type=str, default="syn", 
                        choices=["syn", "mix"])
    parser.add_argument('-tm', "--task_mode", type=str, default="I2I", 
                        choices=["T2I", "I2I"])
    parser.add_argument('-ug', "--use_generated", type=bool, default=False)
    parser.add_argument('-dev', "--device", type=str, default="cuda", 
                        choices=["cpu", "cuda"])
    parser.add_argument('-did', "--device_id", type=str, default="0")
    parser.add_argument('-ab', "--auto_break", type=bool, default=False)
    parser.add_argument('-tc', "--top_count", type=int, default=20, 
                        help="For auto_break")
    parser.add_argument('-T', "--times", type=int, default=1, 
                        help="Running times")
    parser.add_argument('-eg', "--eval_gap", type=int, default=1, 
                        help="Rounds gap for evaluation")
    parser.add_argument('-ddir', "--dataset_dir", type=str, default='./dataset', 
                        help="A directory to save dataset")
    parser.add_argument('-iter', "--iterations", type=int, default=100)
    parser.add_argument('-eps', "--epsilon", type=float, default=5.0, 
                        help="Privacy budget")
    parser.add_argument('-rvpl', "--real_volume_per_label", type=int, default=0)
    parser.add_argument('-ims', "--image_max_size", type=int, default=256)
    parser.add_argument('-vpl', "--volume_per_label", type=int, default=1)
    parser.add_argument('-sgen', "--server_generator", type=str, default="StableDiffusion", 
                        choices=["StableDiffusion", "StableDiffusionXL", "OpenJourney"])
    parser.add_argument('-nipp', "--num_images_per_prompt", type=int, default=1)
    parser.add_argument('-dn', "--do_norm", type=bool, default=False)
    parser.add_argument('-tr', "--test_ratio", type=float, default=0.2, 
                        help="Used when the test set is not originally split")
    parser.add_argument('-pml', "--prompt_max_length", type=int, default=77)
    parser.add_argument('-f', "--framework", type=str, default="Feedback")
    parser.add_argument('-r', "--rater", type=str, default="PE")
    parser.add_argument('-cdata', "--client_dataset", type=str, default="EuroSAT")
    parser.add_argument('-cmodel', "--client_model", type=str, default="ResNet18", 
                        help="CLIP, InceptionV3, ViTs, ResNets")
    parser.add_argument('-cmp', "--client_model_pretrained", type=bool, default=False)
    parser.add_argument('-cef', "--client_encoder_fixed", type=bool, default=False)
    parser.add_argument('-cue', "--client_use_embedding", type=str, default="", 
                        help="Refer to client_model")
    parser.add_argument('-cret', "--client_retrain", type=bool, default=False)
    parser.add_argument('-cbs', "--client_batch_size", type=int, default=128)
    parser.add_argument('-clr', "--client_learning_rate", type=float, default=0.001)
    parser.add_argument('-ce', "--client_epochs", type=int, default=100)
    parser.add_argument('-cuf', "--client_use_filtered", type=bool, default=False)
    parser.add_argument('-caf', "--client_accumulate_filter", type=bool, default=False)
    parser.add_argument('-cst', "--client_send_topk", type=bool, default=False)
    parser.add_argument('-ctpl', "--client_topk_per_label", type=int, default=10000)
    # GenLLM
    parser.add_argument('-sllm', "--server_llm", type=str, default="", 
                        choices=["", "Llama2", "Llama3"])
    # Img2Cap
    parser.add_argument('-cml', "--caption_max_length", type=int, default=70)
    parser.add_argument('-scap', "--server_captioner", type=str, default="", 
                        choices=["", "BlipBase", "BlipLarge", "LLaVA"])
    # I2I
    parser.add_argument('-is', "--i2i_strength", type=float, default=0.8, 
                        help="[0,1]")
    parser.add_argument('-isa', "--i2i_strength_anneal", type=float, default=0.02)
    parser.add_argument('-isth', "--i2i_strength_threshold", type=float, default=0.6)
    parser.add_argument('-uipa', "--use_IPAdapter", type=bool, default=False)
    parser.add_argument('-ipas', "--IPAdapter_scale", type=float, default=0.2, 
                        help="[0,1]")
    # RF
    parser.add_argument('-dth', "--dist_threshold", type=float, default=0.0)
    # PE
    parser.add_argument('-hth', "--histogram_threshold", type=int, default=0)

    args = parser.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = args.device_id

    if args.use_generated:
        assert args.timestamp, 'timestamp is required when use_generated=True'

    if args.device == "cuda" and not torch.cuda.is_available():
        print("\ncuda is not avaiable.\n")
        args.device = "cpu"

    if args.task_type == "mix":
        assert args.real_volume_per_label > 0, 'real_volume_per_label should > 0 when task_type == "mix"'

    if args.framework not in ["Filter", "Feedback"]:
        args.iterations = 1
    elif args.framework == "Filter" and not args.client_accumulate_filter:
        args.iterations = 1

    if args.framework == "Filter":
        assert args.client_use_filtered, 'client_use_filtered should be True when framework == "Filter"'

    print("=" * 50)
    for arg in vars(args):
        print(arg, '=',getattr(args, arg))
    print("=" * 50)

    run(args)