
import numpy as np

dist_list       = [0.5, 1, 1.5, 2, 5, 10, 20, 30, 50, 100]
bf              = 96
feat_chs        = 16
fuse_ch_reduce  = 2
simul_stitching = False
no_depth_resz   = False
align_corners   = False
align_corners_nearest = False 

# These camera models are for the grid makers.
# Surrogate camera model.
cam_model_input=dict(
    type='Equirectangular',
    shape_struct=dict(H=512, W=2048),
    latitude_span=( -np.pi/2, 0 ),
    open_span=False,
    in_to_tensor=True, 
    out_to_numpy=False )

cam_model_output=dict(
    type='Equirectangular',
    shape_struct=dict(H=160, W=640),
    latitude_span=( -np.pi/2, 0 ),
    open_span=False,
    in_to_tensor=True, 
    out_to_numpy=False )

conf_map_surrogate_camera_model=dict(
    cam0=cam_model_input,
    cam1=cam_model_input,
    cam2=cam_model_input,
    rig=cam_model_output,
)

# This is for samplers.
# The rotation matrices for the samplers are all embedded in the frame graph.
conf_map_additional_camera_model=dict(
    cv=dict(
        type='Equirectangular',
        shape_struct=dict(H=80, W=320),
        latitude_span=( -np.pi/2, 0 ),
        open_span=False,
        in_to_tensor=True, 
        out_to_numpy=False ),
)

# The frames must be present in the frame graph and have proper transforms associated with them.
map_camera_frame=dict(
    cam0='cif0s', # The "s" suffix is for "surrogate".
    cam1='cif1s',
    cam2='cif2s',
    rig='rifs',
    cv='cv',
)

config=dict(
    globals=dict(
        align_corners=align_corners,
        align_corners_nearest=align_corners_nearest,
        track_running_stats=True,
        relu_type='leaky',
        relu_inplace=False, ),
    model=dict(
        type='SphericalSweepStereoAirMVS',
        # Level at which the Embeddings are Concat'd with the Feature Map
        # Note: To concat w/ the first level, EmbedCatLvl = 1
        freeze=False,
        simul_stitching=simul_stitching,
        feat_ext_config=dict(
            type='SimpleFeatExtraction',
            chs=feat_chs,
            k_sz=3,
            depths=[5, 10],
            feat_unshuf=False,
            norm_type='batch',
        ),
        cv_builder_config=dict(
            type='SphericalSweepStdMasked',
            num_cams=None, #Updated by the Dataset
            feat_chs=feat_chs,
            post_k_sz=3,
            norm_type='batch',
        ),
        cv_regulator_config=dict(
            type='UNetCostVolumeRegulator',
            in_chs= feat_chs,
            num_cams=None, #Updated by the dataset
	        only_one_cam=True,
            sweep_fuse_ch_reduce=fuse_ch_reduce,
            final_chs=1,
            u_depth=3,
            blk_width=4,
            no_depth_resz=no_depth_resz, # Future use.
            norm_type='batch',
            cost_shuf=False,
            simul_stitching=simul_stitching, # TODO: Fix this.
            stage_factor=2,
            cost_k_sz=3,
            keep_last_chs=[], # TODO: ?
            deconv_k_sz=3
        ),
        dist_regressor_config=dict(
            type='DistanceRegressorWithFixedCandidates',
            dist_cands=dist_list,
            bf=bf,
            out_interp=2,
            pre_interp=True,
        ),
    ),
    optimizer=dict(
        type='Adam',
        lr=0.001,
    ),
    dataloader=dict(
        batch_size=2,
        num_workers=1,
        shuffle_train=True,
        shuffle_test=True,
        grid_maker_builder=dict(
            type='SurrogateCameraModelGridMaker',
            fn='manifest.json',
            conf_map_surrogate_camera_model=conf_map_surrogate_camera_model,
        ),
        conf_map_additional_camera_model=conf_map_additional_camera_model,
        train_dataset=dict(
            type='MultiViewCameraModelDataset',
            metadata_fn="metadata.json", # Under the dataset path.
            frame_graph_fn="frame_graph.json", # Under the dataset path.
            conf_dist_blend_func=dict(
                type='BlendBy2ndOrderGradTorch',
                threshold_scaling_factor=0.01,
            ),
            conf_dist_lab_tab=dict(
                type='FixedDistLabelTable',
                dist_list=dist_list,
                bf=bf,
            ),
            map_camera_frame=map_camera_frame,
            cam_key_cv='cv',
            align_corners=align_corners,
            align_corners_nearest=align_corners_nearest,
            data_keys=['training'],
            mask_path='masks.json',
            csv_input_rgb_suffix='_rgb_fisheye',
            csv_rig_rgb_suffix='_rgb_pano',
            csv_rig_dist_suffix='_dist_pano',
        ),
        test_dataset=dict(
            type='MultiViewCameraModelDataset',
            metadata_fn="metadata.json", # Under the dataset path.
            frame_graph_fn="frame_graph.json", # Under the dataset path.
            conf_dist_blend_func=dict(
                type='BlendBy2ndOrderGradTorch',
                threshold_scaling_factor=0.01,
            ),
            conf_dist_lab_tab=dict(
                type='FixedDistLabelTable',
                dist_list=dist_list,
                bf=bf,
            ),
            map_camera_frame=map_camera_frame,
            cam_key_cv='cv',
            align_corners=align_corners,
            align_corners_nearest=align_corners_nearest,
            data_keys=['test'],
            mask_path='masks.json',
            csv_input_rgb_suffix='_rgb_fisheye',
            csv_rig_rgb_suffix='_rgb_pano',
            csv_rig_dist_suffix='_dist_pano',
        ),
    ),
    augmentation=dict(
        type = 'AugmentationSequence',
        transforms=[
	    {
                "type": "ColorJiggle",
                "brightness": 0.02,
                "contrast": 0.02,
                "saturation": 0.02,
                "hue": 0.02,
                "same_on_batch": False,
                "p": 1.0
            },
            {
                "type": "RandomGaussianNoise",
                "mean": 0.0,
                "std": 0.05,
                "same_on_batch": False,
                "p": 1.0
            },
            dict(
                 type='RandomSingleImageMasking',
                 scale=(0.05, 0.20),
                 ratio=(0.3, 3.3),
                 value=0.0,
                 same_on_batch=False,
                 p=1.0
             )
        ]
    ),
    training=dict(
        loss=dict(
            type='WeightedListLoss',
            name='combined_loss',
            loss_func_configs=[
                dict(
                    type='VolumeLoss',
                    name='loss_twohot',
                    bf=bf,
                    dist_list=dist_list,
                ),
                dict(
                    type='SmoothL1Loss',
                    name='loss_l1',
                    value_name='inv_dist',
                    mask_name='mask_dist',
                    flag_masked_loss=True,
                ),
            ],
            weights=[1, 0]
        ),
        max_epochs=150,
    ),
    validation=dict(
        metrics=dict(
            type='ListLoss',
            name='validation_metrics',
            loss_funcs=[
                dict(
                    type='SSIMLoss',
                    name='ssim',
                    value_name='inv_dist',
                    window_sz=5,
                    bf=bf,
                    dist_list=dist_list,
                ),
                dict(
                    type='RMSELoss',
                    name='rmse',
                    value_name='inv_dist',
                    bf=bf,
                    dist_list=dist_list,
                ),
                dict(
                    type='MAELoss',
                    name='mae',
                    value_name='inv_dist',
                    bf=bf,
                    dist_list=dist_list,
                ),
                dict(
                    type='SmoothL1Loss',
                    name='l1',
                    value_name='inv_dist',
                    mask_name='mask_dist',
                    flag_masked_loss=True,
                ),
                dict(
                    type='VolumeLoss',
                    name='twohot',
                    bf=bf,
                    dist_list=dist_list,
                ),
            ]
        )
    )
)
