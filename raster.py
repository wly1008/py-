# -*- coding: utf-8 -*-
"""
Created on Fri Jun  9 09:31:52 2023

@author: wly
"""

import mycode.code as cd
import re
from functools import partial
import rasterio
import pandas as pd
import numpy as np
from rasterio.enums import Resampling
import os,sys











def get_RasterArrt(raster_in, *args,ds={}, **kwargs):
    
    """
    获得栅格数据属性
    
    raster_in: 栅格地址或栅格数据
    args: 所需属性或函数（类中存在的，输入属性名、函数名即可）
    ds: （dict）传递操作所需变量,可将全局变量（globals()先赋予一个变量，直接将globals()填入参数可能会报错）输入，默认变量为此文件及cd文件的全局变量
    
    
    kwargs: 字典值获得对应属性所需操作，可为表达式，默认参数以字典形式写在“//ks//”之后
            非自身类函数调用时及自身在dic、kwargs中定义的属性调用时，src不可省略。
            必须使用src代表源数据。
            
            合并属性返回类型为list. e.g.'raster_size': ('height', 'width') -> [900, 600]
            如需特定属性请用函数. e.g. 'raster_size': r"(src.height, src.width)" or r"pd.Serise([src.height, src.width])"
   （dic中有部分，按需求添加，可直接修改dic,效果一致,getattrs中ds参数是为传递操作所需变量,如在dic中添加ds需考虑修改函数参数名及系列变动）
    
    ---------------------------------
    return:
        args对应属性值列表

    
    """
    
    ## 输入变量优先级高
    # now = globals()
    # now.update(ds)
    # ds = now
    
    # 此文件变量优先级高
    ds.update(globals())
    
    
    dic = {'raster_size': r"(src.height, src.width)", 'cell_size': ('xsize', 'ysize'),
           'bends': 'count', 'xsize': r'transform[0]', 'ysize': r'abs(src.transform[4])',
           'values': r'src.read().astype(dtype)//ks//{"dtype":np.float64}',
           'df':r'pd.DataFrame(src.values.reshape(-1, 1))'}
    _getattrs = partial(cd.getattrs, **dic)

    if type(raster_in) is rasterio.io.DatasetReader:
        src = raster_in
        
        return _getattrs(src,*args,ds=ds,**kwargs)

    else:
        path_in = raster_in
        with rasterio.open(path_in) as src:
            
            return _getattrs(src, *args, ds=ds, **kwargs)





def add_attrs_raster(src,ds={},**kwargs):
    dic = {'raster_size': r"(src.height, src.width)", 'cell_size': ('xsize', 'ysize'),
           'bends': 'count', 'xsize': r'transform[0]', 'ysize': r'abs(src.transform[4])',
           'values': r'src.read().astype(dtype)//ks//{"dtype":np.float64}',
           'df':r'pd.DataFrame(src.values.reshape(-1, 1))'}
    
    dic.update(kwargs)
    
    data = globals()
    data.update(ds)
    ds = data
    
    cd.add_attrs(src, run=True, ds=ds,**dic)





def read(raster_in, n=1, tran=True, nan=np.nan, dtype=np.float64, driver='GTiff', 
         re_shape=False, re_scale=False, re_size=False, how='nearest', printf=False):
    """

    raster_in : 
        栅格地址或栅格数据
    n : 1 or 2 or 3, optional.
        返回几个值. The default is 1.
    tran : bool, optional.
        是否变为单列. The default is True.
    nan : optional
        无效值设置.The default is np.nan.
    dtype : 数据类型转换函数，optional
        矩阵值的格式. The default is np.float64.

    ---------------------------------------------------------------------------


    重采样参数（re_shape=False, re_scale=False, re_size=False, how='nearest',printf=False）



    re_shape:形状重采样(tuple)
    (count, height, width)

    re_size:大小重采样(tuple or number)
    (xsize,ysize) or size

    re_scale:倍数重采样(number)
    scale = 目标边长大小/源数据边长大小


    how:(str or int) , optional.
    重采样方式，The default is nearest.

    (部分)
    mode:众数，6;
    nearest:临近值，0;
    bilinear:双线性，1;
    cubic_spline:三次卷积，3。
    ...其余见rasterio.enums.Resampling




    printf : 任意值,optional.
        如果发生重采样，则会打印原形状及输入值。The default is False.

    ---------------------------------------------------------------------------


    Returns:
        栅格矩阵（单列or原型）；profile;shape

    """

    def update():  # <<<<<<<<<更新函数

        if shape != out_shape:

            if not (printf is False):
                print(f'{printf}的原形状为{shape}')

            bounds = {'west': west, 'south': south, 'east': east,
                      'north': north, 'height': out_shape[1], 'width': out_shape[2]}

            transform = rasterio.transform.from_bounds(**bounds)

            profile.data.update({'height': out_shape[1], 'width': out_shape[2], 'transform': transform})

            if type(how) is int:
                _resampling = how
            else:
                _resampling = getattr(Resampling, how)

            data = src.read(out_shape=out_shape, resampling=_resampling).astype(dtype)
        else:
            data = src.read().astype(dtype)

        return data
    
    
    if type(raster_in) is rasterio.io.DatasetReader:
        src = raster_in 
    else:
        src = rasterio.open(raster_in)

    # 取出所需参数
    nodata, profile, count, height, width, transform = get_RasterArrt(src, *(
                        'nodata', 'profile', 'count', 'height', 'width', 'transform'))
    
    

    west, south, east, north = rasterio.transform.array_bounds(height, width, transform)
    nodata = dtype(nodata)
    shape = (count, height, width)

    # 获得矩阵;更新profile、shape

    if re_shape:
        out_shape = re_shape

        # 更新
        data = update()
        shape = out_shape


    elif re_size:

        if (type(re_size) == int) | (type(re_size) == float):
            xsize = re_size
            ysize = re_size
        else:
            xsize, ysize = re_size
        out_shape = (count, int((north - south) / ysize), int((east - west) / xsize))

        # 更新
        data = update()
        shape = out_shape



    elif re_scale:
        scale = re_scale
        out_shape = (count, int(height / scale), int(width / scale))

        # 更新
        data = update()
        shape = out_shape


    else:
        data = src.read().astype(dtype)

    profile.data.update({'nodata': nan, 'dtype': dtype, 'driver': driver})

    # 处理无效值
    data = data.reshape(-1, 1)
    data = pd.DataFrame(data)
    data.replace(nodata, nan, inplace=True)

    # 变形
    if tran:
        pass
    else:
        data = np.array(data).reshape(shape)
        if shape[0] == 1:
            data = pd.DataFrame(data[0])

    src.close()

    # 返回
    if n == 1:
        return data
    elif n == 2:
        return data, profile
    elif n == 3:
        return data, profile, shape
    else:
        print('n=1 or 2 or 3')


def out(out_path, data, pro, shape):
    """
    操作函数
    ---------

    输出文件函数

    """
    data = np.array(data).reshape(shape)
    bend = shape[0]
    with rasterio.open(out_path, 'w', **pro) as src:
        for i in range(bend):
            src.write(data[i], i + 1)


def mask(path_in, path_mask, out_path):
    """
    操作函数，会直接输出
    ---------------------

    需保证('crs', 'raster_size', 'transform')一致才能正常使用

    -----------------------------------

    栅格提取栅格，在掩膜（mask）中有效值的位置，输入栅格（path_in）的相应位置值会被保留


    """

    df_tif, pro, shape = read(path_in, 3)
    df_mask, pro_m, shape_m = read(path_mask, 3)

    arrtnames = ('crs', 'raster_size', 'transform')


    arrt = get_RasterArrt(path_in, arrtnames)
    arrt_m = get_RasterArrt(path_mask, arrtnames)

    if not arrt == arrt_m:
        for i in range(len(arrt)):
            if arrt[i] != arrt_m[i]:
                print(f'{arrtnames[i]}不同')



    bends = get_RasterArrt(path_in, 'bands')
    bends_m = get_RasterArrt(path_mask, 'bands')

    df_mask1 = df_mask.iloc[:len(df_mask)/bends_m]
    df_maskx = pd.DataFrame()
    for i in range(bends):
        df_maskx = pd.concat([df_maskx, df_mask1])
    mask = ~df_maskx.isna()

    df = df_tif[mask]

    out(out_path, df, pro, shape)


def resampling(path_in, out_path, nan=np.nan, dtype=np.float64, driver='GTiff', 
               re_shape=False, re_scale=False, re_size=False, how='nearest', printf=False):
    """
    操作函数，直接输出
    ------------------------------------

    重采样，参数详见read、out

    """

    data, pro, shape = read(path_in, n=3, nan=nan, dtype=dtype, driver=driver, 
                            re_size=re_size, re_scale=re_scale, re_shape=re_shape,
                            how=how, printf=printf)

    out(out_path, data, pro, shape)









    
    
    
    
    
    
    
    

dic = {'raster_size': r"(src.height, src.width)", 'cell_size': ('xsize', 'ysize'),
       'bends': 'count', 'xsize': r'transform[0]', 'ysize': r'abs(src.transform[4])',
       'values': r'src.read().astype(dtype)//ks//{"dtype":np.float64}',
       'df':r'pd.DataFrame(src.values.reshape(-1, 1))'}


path_in = r'F:\PyCharm\pythonProject1\arcmap\007那曲市\data\eva平均\eva_2.tif'
src = rasterio.open(path_in)


get_RasterArrt(src,*['bends', 'cell_size', 'df', 'raster_size', 'values', 'xsize', 'ysize'])





















