from osgeo import gdal
import numpy as np
import glob
import os
import re

def read_img(filename):
        dataset = gdal.Open(filename)
        im_width = dataset.RasterXSize #栅格矩阵的列数
        im_height = dataset.RasterYSize #栅格矩阵的行数
        im_geotrans = dataset.GetGeoTransform() #仿射矩阵
        im_proj = dataset.GetProjection() #地图投影
        im_data = dataset.ReadAsArray(0,0,im_width,im_height)
        del dataset
        return im_proj,im_geotrans,im_data

def write_img(filename,im_proj,im_geotrans,im_data):
        if "int8" in im_data.dtype.name:
            datatype = gdal.GDT_Byte
        if "int16" in im_data.dtype.name:
            datatype = gdal.GDT_UInt16
        else:
            datatype = gdal.GDT_Float32

        if len(im_data.shape) == 3:
            im_bands, im_height, im_width = im_data.shape
        else:
            im_bands, (im_height, im_width) = 1, im_data.shape

        driver = gdal.GetDriverByName("GTiff")  # 数据类型必须有，因为要计算需要多大内存空间
        dataset = driver.Create(filename, im_width, im_height, im_bands, datatype)

        dataset.SetGeoTransform(im_geotrans)  # 写入仿射变换参数
        dataset.SetProjection(im_proj)  # 写入投影

        if im_bands == 1:
            dataset.GetRasterBand(1).WriteArray(im_data)  # 写入数组数据
        else:
            for i in range(im_bands):
                dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
        del dataset

        
et_path  = 'F:\\SCI\\CESM\\'
et_list = glob.glob(os.path.join(et_path, 'CESM2.HIS.AODVIS.*.tif'))
proj = read_img("F:\\SCI\\CESM\\CESM2.HIS.AODVIS.1980-01.tif")[0]
geotrans = read_img("F:\\SCI\\CESM\\CESM2.HIS.AODVIS.1980-01.tif")[1]
annualmean = []

for y_idx in range(1980, 2015):
    for m_idx in range(1, 13):
        for et_name in et_list:
            # 获取文件名中日期信息
            #name = re.findall(r'MOD16A2GF.A(\d{7}).h28v06', path.basename(et_name))[0]
            #date = datetime.datetime.strptime(name, '%Y%j')
            #year, month, day = date.year, date.month, date.day
            date = re.findall(r'....-..',et_name)
            syear = date[0][0:4]
            smonth = date[0][-2:]
            year = int(date[0][0:4])
            month = int(date[0][-2:])
            if year == y_idx:
                if month == m_idx:
                    a1 = read_img(f"F:\\SCI\\CESM\\CESM2.HIS.AODVIS.{syear}-{smonth}.tif")[2]
                    a1 = a1.astype(np.float32)
                    a1[np.where(a1 <= -3.3e+38)]=np.nan
                    # 同一年相同月份的影像存放一起并插入各景影像数据在各月份中所占权重
                    # 根据所占月份时间长短确定权重（暂时设为1）
                    if m_idx == 1:
                        m_array = a1
                    elif m_idx ==2:
                        m_array = np.stack([m_array,a1],axis=2)
                    else:
                        m_array = np.insert(m_array,0,a1,axis=2)
                    break
    mean_array = np.nanmean(m_array,axis=2)
    write_img(f"aodmean/{year}AODmean.tif",proj,geotrans,mean_array)
    annualmean.append(np.nanmean(mean_array))
    if y_idx == 1980:
        y_array = mean_array
    elif y_idx == 1981:
        y_array = np.stack([y_array,mean_array],axis=2)
    else:
        y_array = np.insert(y_array,0,mean_array,axis=2)

y_array = np.nanmean(y_array,axis=2)
write_img("aodmean/AODmean.tif",proj,geotrans,y_array)
print(annualmean)
