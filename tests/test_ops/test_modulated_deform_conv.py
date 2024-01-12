# Copyright (c) OpenMMLab. All rights reserved.
import os

import numpy
import pytest
import torch
from mmengine.utils import digit_version
from mmengine.utils.dl_utils import TORCH_VERSION

from mmcv.utils import IS_CUDA_AVAILABLE, IS_MLU_AVAILABLE, IS_MUSA_AVAILABLE

try:
    # If PyTorch version >= 1.6.0 and fp16 is enabled, torch.cuda.amp.autocast
    # would be imported and used; we should test if our modules support it.
    from torch.cuda.amp import autocast
except ImportError:
    pass

cur_dir = os.path.dirname(os.path.abspath(__file__))

input_t = [[[[1., 2., 3.], [1., 2., 3.], [1., 2., 3.]]]]
output_t = [[[[0.5, 1.5, 2.5, 1.5], [1.0, 3.0, 5.0, 3.0], [1.0, 3.0, 5.0, 3.0],
              [0.5, 1.5, 2.5, 1.5]]]]
input_grad = [[[[2., 2., 2.], [2., 2., 2.], [2., 2., 2.]]]]
dcn_w_grad = [[[[9., 9.], [9., 9.]]]]
dcn_offset_w_grad = [[[[-7.0, -4.0], [0.0, 0.0]]], [[[-9.0, 7.5], [-6.0,
                                                                   5.0]]],
                     [[[-4.0, -7.0], [0.0, 0.0]]],
                     [[[-7.5, -9.0], [-5.0, -6.0]]],
                     [[[-7.0, -4.0], [-7.0, -4.0]]],
                     [[[-6.0, 5.0], [-9.0, 7.5]]],
                     [[[-4.0, -7.0], [-4.0, -7.0]]],
                     [[[-5.0, -6.0], [-7.5, -9.0]]], [[[10.5, 6.0], [7.0,
                                                                     4.0]]],
                     [[[6.0, 10.5], [4.0, 7.0]]], [[[7.0, 4.0], [10.5, 6.0]]],
                     [[[4.0, 7.0], [6.0, 10.5]]]]
dcn_offset_b_grad = [
    -3.0, -1.5, -3.0, -1.5, -3.0, -1.5, -3.0, -1.5, 4.5, 4.5, 4.5, 4.5
]


class TestMdconv:

    def _test_mdconv(self, device, dtype=torch.float):
        if (not torch.cuda.is_available() and device
                == 'cuda') and (not IS_MUSA_AVAILABLE and device == 'musa'):
            pytest.skip('test requires GPU')
        if device == 'mlu':
            from mmcv.ops import \
                ModulatedDeformConv2dPack_MLU as ModulatedDeformConv2dPack
        else:
            from mmcv.ops import ModulatedDeformConv2dPack

        input = torch.tensor(input_t, dtype=dtype, device=device)
        input.requires_grad = True

        dcn = ModulatedDeformConv2dPack(
            1,
            1,
            kernel_size=(2, 2),
            stride=1,
            padding=1,
            deform_groups=1,
            bias=False).to(device)

        dcn.weight.data.fill_(1.)
        dcn.type(dtype)
        output = dcn(input)
        output.sum().backward()
        assert numpy.allclose(output.cpu().detach().numpy(), output_t, 1e-2)
        assert numpy.allclose(input.grad.cpu().detach().numpy(), input_grad,
                              1e-2)
        assert numpy.allclose(dcn.weight.grad.cpu().detach().numpy(),
                              dcn_w_grad, 1e-2)
        assert numpy.allclose(
            dcn.conv_offset.weight.grad.cpu().detach().numpy(),
            dcn_offset_w_grad, 1e-2)
        assert numpy.allclose(dcn.conv_offset.bias.grad.cpu().detach().numpy(),
                              dcn_offset_b_grad, 1e-2)

    def _test_amp_mdconv(self, input_dtype=torch.float, device='cuda'):
        """The function to test amp released on pytorch 1.6.0.

        The type of input data might be torch.float or torch.half,
        so we should test mdconv in both cases. With amp, the data
        type of model will NOT be set manually.

        Args:
            input_dtype: torch.float or torch.half.
        """
        if not torch.cuda.is_available() and device == 'cuda':
            return
        if device == 'mlu':
            from mmcv.ops import \
                ModulatedDeformConv2dPack_MLU as ModulatedDeformConv2dPack
        else:
            from mmcv.ops import ModulatedDeformConv2dPack

        input = torch.tensor(input_t).to(device).type(input_dtype)
        input.requires_grad = True

        dcn = ModulatedDeformConv2dPack(
            1,
            1,
            kernel_size=(2, 2),
            stride=1,
            padding=1,
            deform_groups=1,
            bias=False).to(device)
        dcn.weight.data.fill_(1.)
        output = dcn(input)
        output.sum().backward()
        assert numpy.allclose(output.cpu().detach().numpy(), output_t, 1e-2)
        assert numpy.allclose(input.grad.cpu().detach().numpy(), input_grad,
                              1e-2)
        assert numpy.allclose(dcn.weight.grad.cpu().detach().numpy(),
                              dcn_w_grad, 1e-2)
        assert numpy.allclose(
            dcn.conv_offset.weight.grad.cpu().detach().numpy(),
            dcn_offset_w_grad, 1e-2)
        assert numpy.allclose(dcn.conv_offset.bias.grad.cpu().detach().numpy(),
                              dcn_offset_b_grad, 1e-2)

    @pytest.mark.parametrize('device', [
        'cpu',
        pytest.param(
            'cuda',
            marks=pytest.mark.skipif(
                not IS_CUDA_AVAILABLE, reason='requires CUDA support')),
        pytest.param(
            'musa',
            marks=pytest.mark.skipif(
                not IS_MUSA_AVAILABLE, reason='requires MUSA support')),
        pytest.param(
            'mlu',
            marks=pytest.mark.skipif(
                not IS_MLU_AVAILABLE, reason='requires MLU support')),
    ])
    def test_mdconv_float(self, device):
        self._test_mdconv(dtype=torch.float, device=device)

    @pytest.mark.parametrize('device', [
        'cpu',
        pytest.param(
            'cuda',
            marks=pytest.mark.skipif(
                not IS_CUDA_AVAILABLE, reason='requires CUDA support')),
        pytest.param(
            'musa',
            marks=pytest.mark.skipif(
                not IS_MUSA_AVAILABLE, reason='requires MUSA support')),
        pytest.param(
            'mlu',
            marks=pytest.mark.skipif(
                not IS_MLU_AVAILABLE, reason='requires MLU support')),
    ])
    def test_mdconv_double(self, device):
        # TODO haowen.han@mthreads.com:not supported by musa yet!
        if IS_MUSA_AVAILABLE:
            return
        self._test_mdconv(dtype=torch.double, device=device)

    @pytest.mark.parametrize('device', [
        pytest.param(
            'cuda',
            marks=pytest.mark.skipif(
                not IS_CUDA_AVAILABLE, reason='requires CUDA support')),
        pytest.param(
            'mlu',
            marks=pytest.mark.skipif(
                not IS_MLU_AVAILABLE, reason='requires MLU support')),
    ])
    def test_mdconv_half(self, device):
        self._test_mdconv(torch.half, device=device)

        # test amp when torch version >= '1.6.0', the type of
        # input data for mdconv might be torch.float or torch.half
        if (TORCH_VERSION != 'parrots'
                and digit_version(TORCH_VERSION) >= digit_version('1.6.0')):
            with autocast(enabled=True):
                self._test_amp_mdconv(torch.float, device=device)
                self._test_amp_mdconv(torch.half, device=device)
