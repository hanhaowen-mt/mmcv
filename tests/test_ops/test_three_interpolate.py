# Copyright (c) OpenMMLab. All rights reserved.
import pytest
import torch

from mmcv.ops import three_interpolate
from mmcv.utils import IS_CUDA_AVAILABLE, IS_MUSA_AVAILABLE, IS_NPU_AVAILABLE


@pytest.mark.parametrize('dtype', [
    pytest.param(
        torch.half,
        marks=pytest.mark.skipif(
            IS_MUSA_AVAILABLE, reason='MUSA does not support for half yet!')),
    torch.float,
    pytest.param(
        torch.double,
        marks=pytest.mark.skipif(
            IS_NPU_AVAILABLE or IS_MUSA_AVAILABLE,
            reason='NPU does not support for 64-bit floating point'))
])
@pytest.mark.parametrize('device', [
    pytest.param(
        'cuda',
        marks=pytest.mark.skipif(
            not IS_CUDA_AVAILABLE, reason='requires CUDA support')),
    pytest.param(
        'npu',
        marks=pytest.mark.skipif(
            not IS_NPU_AVAILABLE, reason='requires NPU support')),
    pytest.param(
        'musa',
        marks=pytest.mark.skipif(
            not IS_MUSA_AVAILABLE, reason='requires MUSA support'))
])
def test_three_interpolate(dtype, device):
    features = torch.tensor(
        [[[2.4350, 4.7516, 4.4995, 2.4350, 2.4350, 2.4350],
          [3.1236, 2.6278, 3.0447, 3.1236, 3.1236, 3.1236],
          [2.6732, 2.8677, 2.6436, 2.6732, 2.6732, 2.6732],
          [0.0124, 7.0150, 7.0199, 0.0124, 0.0124, 0.0124],
          [0.3207, 0.0000, 0.3411, 0.3207, 0.3207, 0.3207]],
         [[0.0000, 0.9544, 2.4532, 0.0000, 0.0000, 0.0000],
          [0.5346, 1.9176, 1.4715, 0.5346, 0.5346, 0.5346],
          [0.0000, 0.2744, 2.0842, 0.0000, 0.0000, 0.0000],
          [0.3414, 1.5063, 1.6209, 0.3414, 0.3414, 0.3414],
          [0.5814, 0.0103, 0.0000, 0.5814, 0.5814, 0.5814]]],
        dtype=dtype,
        device=device)

    idx = torch.tensor(
        [[[0, 1, 2], [2, 3, 4], [2, 3, 4], [0, 1, 2], [0, 1, 2], [0, 1, 3]],
         [[0, 2, 3], [1, 3, 4], [2, 1, 4], [0, 2, 4], [0, 2, 4], [0, 1, 2]]],
        device=device).int()

    weight = torch.tensor([[[3.3333e-01, 3.3333e-01, 3.3333e-01],
                            [1.0000e+00, 5.8155e-08, 2.2373e-08],
                            [1.0000e+00, 1.7737e-08, 1.7356e-08],
                            [3.3333e-01, 3.3333e-01, 3.3333e-01],
                            [3.3333e-01, 3.3333e-01, 3.3333e-01],
                            [3.3333e-01, 3.3333e-01, 3.3333e-01]],
                           [[3.3333e-01, 3.3333e-01, 3.3333e-01],
                            [1.0000e+00, 1.3651e-08, 7.7312e-09],
                            [1.0000e+00, 1.7148e-08, 1.4070e-08],
                            [3.3333e-01, 3.3333e-01, 3.3333e-01],
                            [3.3333e-01, 3.3333e-01, 3.3333e-01],
                            [3.3333e-01, 3.3333e-01, 3.3333e-01]]],
                          dtype=dtype,
                          device=device)

    output = three_interpolate(features, idx, weight)
    expected_output = torch.tensor([[[
        3.8953e+00, 4.4995e+00, 4.4995e+00, 3.8953e+00, 3.8953e+00, 3.2072e+00
    ], [
        2.9320e+00, 3.0447e+00, 3.0447e+00, 2.9320e+00, 2.9320e+00, 2.9583e+00
    ], [
        2.7281e+00, 2.6436e+00, 2.6436e+00, 2.7281e+00, 2.7281e+00, 2.7380e+00
    ], [
        4.6824e+00, 7.0199e+00, 7.0199e+00, 4.6824e+00, 4.6824e+00, 2.3466e+00
    ], [
        2.2060e-01, 3.4110e-01, 3.4110e-01, 2.2060e-01, 2.2060e-01, 2.1380e-01
    ]],
                                    [[
                                        8.1773e-01, 9.5440e-01, 2.4532e+00,
                                        8.1773e-01, 8.1773e-01, 1.1359e+00
                                    ],
                                     [
                                         8.4689e-01, 1.9176e+00, 1.4715e+00,
                                         8.4689e-01, 8.4689e-01, 1.3079e+00
                                     ],
                                     [
                                         6.9473e-01, 2.7440e-01, 2.0842e+00,
                                         6.9473e-01, 6.9473e-01, 7.8619e-01
                                     ],
                                     [
                                         7.6789e-01, 1.5063e+00, 1.6209e+00,
                                         7.6789e-01, 7.6789e-01, 1.1562e+00
                                     ],
                                     [
                                         3.8760e-01, 1.0300e-02, 8.3569e-09,
                                         3.8760e-01, 3.8760e-01, 1.9723e-01
                                     ]]],
                                   dtype=dtype,
                                   device=device)
    assert torch.allclose(output, expected_output, 1e-3, 1e-4)
