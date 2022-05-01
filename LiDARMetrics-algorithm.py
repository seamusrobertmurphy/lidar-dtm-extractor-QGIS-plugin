"""
Model exported as python.
Name : LiDAR Metrics Extraction
Group : EFI-CRM
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterMultipleLayers
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class LidarMetricsExtraction(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('areaextent', 'AOI Boundary', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        # https://maps.canada.ca/czs/index-en.html
        self.addParameter(QgsProcessingParameterMultipleLayers('demtiles', 'DEM Tiles', layerType=QgsProcessing.TypeRaster, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSource('faibplots', 'FAIB PSP plots', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        # https://catalogue.data.gov.bc.ca/dataset/cff7b8f7-6897-444f-8c53-4bb93c7e9f8b
        self.addParameter(QgsProcessingParameterVectorLayer('harvestmask20yrs', 'Harvest Cutblocks', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        # Choose from "Fir" or "Pine" or "Spruce"
        self.addParameter(QgsProcessingParameterString('speciessubzone', 'Species-Group', multiLine=False, defaultValue='Fir'))
        # https://catalogue.data.gov.bc.ca/dataset/vri-2020-forest-vegetation-composite-rank-1-layer-r1-/resource/d91bf7df-7c5f-49e0-b206-d3a87bc354f9
        self.addParameter(QgsProcessingParameterFeatureSource('specieszones', 'Vegetated Resource Index (VRI)', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        # https://catalogue.data.gov.bc.ca/dataset/22c7cb44-1463-48f7-8e47-88857f207702
        self.addParameter(QgsProcessingParameterVectorLayer('voidsdisturbanceroads', 'Voids & Disturbances', optional=True, types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Output1RasterPredicterOfNorthnessIndexClippedToExtentOfUserselectedVriLeadspeciesArea', 'Output 1.  Raster Predicter of Northness Index clipped to extent of user-selected VRI lead-species area', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Output2RasterPredicterOfSlope_classClippedToExtentOfUserselectedVriLeadspeciesZone', 'Output 2.  Raster Predicter of Slope_Class clipped to extent of user-selected VRI lead-species zone', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Output3TrainingPointsWithExtractedLidarMetricsAndSubsampledBySpeciesGroupOfMerchantableSizecAndLocatedAcrossVriLeadspeciesZonesOfAoi', 'Output 3. Training points with extracted LiDAR metrics and subsampled by species group of merchantable sizec and located across VRI lead-species zones of AOI', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(21, model_feedback)
        results = {}
        outputs = {}

        # Clip VRI layer to AOI Boundary
        alg_params = {
            'EXTENT': parameters['voidsdisturbanceroads'],
            'INPUT': parameters['specieszones'],
            'OPTIONS': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ClipVriLayerToAoiBoundary'] = processing.run('gdal:clipvectorbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Filter cutblocks using inverted mask of <20yrs pre-LiDAR harvests
        alg_params = {
            'INPUT': parameters['areaextent'],
            'OVERLAY': parameters['harvestmask20yrs'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FilterCutblocksUsingInvertedMaskOf20yrsPrelidarHarvests'] = processing.run('native:difference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Species-Zones (Vector)
        # case
when "SPEC_CD_1" = 'BL' then 'Fir'
when "SPEC_CD_1" = 'FD' then 'Fir'
when "SPEC_CD_1" = 'FDI' then 'Fir'
when "SPEC_CD_1" = 'PL' then 'Pine'
when "SPEC_CD_1" = 'PLI' then 'Pine'
when "SPEC_CD_1" = 'SW' then 'Spruce'
when "SPEC_CD_1" = 'SE' then 'Spruce'
when "SPEC_CD_1" = 'SX' then 'Spruce'
else 'Broadleaf'
end




        alg_params = {
            'FIELDS_MAPPING': [{'expression': 'case\nwhen "SPEC_CD_1" = \'BL\' then \'Fir\'\nwhen "SPEC_CD_1" = \'FD\' then \'Fir\'\nwhen "SPEC_CD_1" = \'FDI\' then \'Fir\'\nwhen "SPEC_CD_1" = \'PL\' then \'Pine\'\nwhen "SPEC_CD_1" = \'PLI\' then \'Pine\'\nwhen "SPEC_CD_1" = \'SW\' then \'Spruce\'\nwhen "SPEC_CD_1" = \'SE\' then \'Spruce\'\nwhen "SPEC_CD_1" = \'SX\' then \'Spruce\'\nelse \'Broadleaf\'\nend\n\n\n\n','length': 6,'name': 'Species-Zones','precision': 0,'type': 10}],
            'INPUT': outputs['ClipVriLayerToAoiBoundary']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SpecieszonesVector'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Mosaic DEM Tiles
        alg_params = {
            'ADD_ALPHA': False,
            'ASSIGN_CRS': None,
            'EXTRA': '',
            'INPUT': parameters['demtiles'],
            'PROJ_DIFFERENCE': False,
            'RESAMPLING': 0,  # Nearest Neighbour
            'RESOLUTION': 0,  # Average
            'SEPARATE': False,
            'SRC_NODATA': '-9999',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MosaicDemTiles'] = processing.run('gdal:buildvirtualraster', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Species Selection
        alg_params = {
            'FIELD': parameters['speciessubzone'],
            'INPUT': outputs['SpecieszonesVector']['OUTPUT'],
            'OPERATOR': 0,  # =
            'VALUE': 'SpeciesZones',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SpeciesSelection'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Filter outlier scrubland,  roads, burn sites,  beetles etc.
        alg_params = {
            'INPUT': outputs['FilterCutblocksUsingInvertedMaskOf20yrsPrelidarHarvests']['OUTPUT'],
            'OVERLAY': parameters['voidsdisturbanceroads'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FilterOutlierScrublandRoadsBurnSitesBeetlesEtc'] = processing.run('native:difference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Subset FAIB plots by VRI species zones 
        alg_params = {
            'INPUT': parameters['faibplots'],
            'INTERSECT': outputs['SpeciesSelection']['OUTPUT'],
            'PREDICATE': [4],  # touch
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SubsetFaibPlotsByVriSpeciesZones'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Warp (reproject)
        # https://catalogue.data.gov.bc.ca/dataset/8daa29da-d7f4-401c-83ae-d962e3a28980
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['MosaicDemTiles']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': -9999,
            'OPTIONS': '',
            'RESAMPLING': 0,  # Nearest Neighbour
            'SOURCE_CRS': None,
            'TARGET_CRS': parameters['areaextent'],
            'TARGET_EXTENT': parameters['areaextent'],
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': 20,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['WarpReproject'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Species-Subzone (Raster)
        alg_params = {
            'BURN': None,
            'DATA_TYPE': 5,  # Float32
            'EXTENT': outputs['SpecieszonesVector']['OUTPUT'],
            'EXTRA': '',
            'FIELD': '',
            'HEIGHT': 20,
            'INIT': None,
            'INPUT': outputs['SpeciesSelection']['OUTPUT'],
            'INVERT': False,
            'NODATA': None,
            'OPTIONS': '',
            'UNITS': 0,  # Pixels
            'USE_Z': False,
            'WIDTH': 20,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SpeciessubzoneRaster'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Extract FAIB plots of merchantable size for each species
        # ("species_class" = 'Spruce' OR 'Douglas-Fir' OR 'TrueFir' AND "lead_htop" >= 17.5) OR ("species_class" = 'Pine' AND "lead_htop" >= 12.5)
        alg_params = {
            'EXPRESSION': '("species_class" = \'Spruce\' OR \'Douglas-Fir\' OR \'TrueFir\' AND "lead_htop" >= 17.5) OR ("species_class" = \'Pine\' AND "lead_htop" >= 12.5)\n\n',
            'INPUT': outputs['SubsetFaibPlotsByVriSpeciesZones']['OUTPUT'],
            'FAIL_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractFaibPlotsOfMerchantableSizeForEachSpecies'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Fill nodata cells
        alg_params = {
            'BAND': 1,
            'DISTANCE': 10,
            'EXTRA': '',
            'INPUT': outputs['WarpReproject']['OUTPUT'],
            'ITERATIONS': 0,
            'MASK_LAYER': None,
            'NO_MASK': False,
            'OPTIONS': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FillNodataCells'] = processing.run('gdal:fillnodata', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Slope_degree
        # Parameters: 
Input = Projected DEM Mosaic,  
Slope = degrees,  V:H = 1.00,  
Edges = uncomputed,  
Formula=Zevenbergen&Thorne
        alg_params = {
            'AS_PERCENT': False,
            'BAND': 1,
            'COMPUTE_EDGES': False,
            'EXTRA': '',
            'INPUT': outputs['FillNodataCells']['OUTPUT'],
            'OPTIONS': '',
            'SCALE': 1,
            'ZEVENBERGEN': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope_degree'] = processing.run('gdal:slope', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Slope_Tan%
        # (tan(slope_degree)*100)
        alg_params = {
            'BAND_A': 1,
            'BAND_B': None,
            'BAND_C': None,
            'BAND_D': None,
            'BAND_E': None,
            'BAND_F': None,
            'EXTRA': '',
            'FORMULA': '(tan(\'"Slope@1" from algorithm "Slope_degree"\')*100)',
            'INPUT_A': outputs['Slope_degree']['OUTPUT'],
            'INPUT_B': None,
            'INPUT_C': None,
            'INPUT_D': None,
            'INPUT_E': None,
            'INPUT_F': None,
            'NO_DATA': -999,
            'OPTIONS': '',
            'RTYPE': 5,  # Float32
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope_tan'] = processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Aspect_degree
        # Parameters: 
Input = Projected DEM Mosaic,  
Aspect = azimuth,  Flat = -999  
Edges = uncomputed,  
Formula = Zevenbergen & Thorne
        alg_params = {
            'BAND': 1,
            'COMPUTE_EDGES': False,
            'EXTRA': '',
            'INPUT': outputs['FillNodataCells']['OUTPUT'],
            'OPTIONS': '',
            'TRIG_ANGLE': False,
            'ZERO_FLAT': False,
            'ZEVENBERGEN': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Aspect_degree'] = processing.run('gdal:aspect', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Fill sinks (Wang & Liu)
        alg_params = {
            'ELEV': outputs['FillNodataCells']['OUTPUT'],
            'MINSLOPE': 0.01,
            'FDIR': QgsProcessing.TEMPORARY_OUTPUT,
            'FILLED': QgsProcessing.TEMPORARY_OUTPUT,
            'WSHED': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FillSinksWangLiu'] = processing.run('saga:fillsinkswangliu', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Northness_index
        # 0.0 thru 22.499 = 1.0
22.5 thru 67.499 = 0.5
67.5 thru 112.499 = 0.0	
112.5 thru 157.499 = -0.5
157.5 thru 202.499 = -1.0
202.5 thru 247.499 = -0.5
247.5 thru 292.499 = 0.0
292.5 thru 337.499 = 0.5
337.5 thru 360.5 = 1.0
        alg_params = {
            'DATA_TYPE': 5,  # Float32
            'INPUT_RASTER': outputs['Aspect_degree']['OUTPUT'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': -999,
            'RANGE_BOUNDARIES': 1,  # min <= value < max
            'RASTER_BAND': 1,
            'TABLE': [0,22.49,1.0,22.5,67.49,0.5,67.5,112.49,0.0,112.5,157.49,-0.5,157.5,202.49,-1.0,202.5,247.49,-0.5,247.5,292.49,0.0,292.5,337.49,0.5,337.5,360.5,1],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Northness_index'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Slope_CRMclasses
        alg_params = {
            'DATA_TYPE': 5,  # Float32
            'INPUT_RASTER': outputs['Slope_tan']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 1,  # min <= value < max
            'RASTER_BAND': 1,
            'TABLE': [0,11.31,1,11.32,16.70,2,16.71,24.23,3,24.24,30.96,4,30.97,100,5],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Slope_crmclasses'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Northness (Clipped to VRI Species Zone)
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['Northness_index']['OUTPUT'],
            'NODATA': -9999,
            'OPTIONS': '',
            'OVERCRS': False,
            'PROJWIN': outputs['SpeciessubzoneRaster']['OUTPUT'],
            'OUTPUT': parameters['Output1RasterPredicterOfNorthnessIndexClippedToExtentOfUserselectedVriLeadspeciesArea']
        }
        outputs['NorthnessClippedToVriSpeciesZone'] = processing.run('gdal:cliprasterbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Output1RasterPredicterOfNorthnessIndexClippedToExtentOfUserselectedVriLeadspeciesArea'] = outputs['NorthnessClippedToVriSpeciesZone']['OUTPUT']

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Clip raster by extent
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['Slope_crmclasses']['OUTPUT'],
            'NODATA': -9999,
            'OPTIONS': '',
            'OVERCRS': False,
            'PROJWIN': outputs['SpeciessubzoneRaster']['OUTPUT'],
            'OUTPUT': parameters['Output2RasterPredicterOfSlope_classClippedToExtentOfUserselectedVriLeadspeciesZone']
        }
        outputs['ClipRasterByExtent'] = processing.run('gdal:cliprasterbyextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Output2RasterPredicterOfSlope_classClippedToExtentOfUserselectedVriLeadspeciesZone'] = outputs['ClipRasterByExtent']['OUTPUT']

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Sample raster values
        alg_params = {
            'COLUMN_PREFIX': 'Northness',
            'INPUT': outputs['ExtractFaibPlotsOfMerchantableSizeForEachSpecies']['FAIL_OUTPUT'],
            'RASTERCOPY': outputs['Northness_index']['OUTPUT'],
            'OUTPUT': parameters['Output3TrainingPointsWithExtractedLidarMetricsAndSubsampledBySpeciesGroupOfMerchantableSizecAndLocatedAcrossVriLeadspeciesZonesOfAoi']
        }
        outputs['SampleRasterValues'] = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Output3TrainingPointsWithExtractedLidarMetricsAndSubsampledBySpeciesGroupOfMerchantableSizecAndLocatedAcrossVriLeadspeciesZonesOfAoi'] = outputs['SampleRasterValues']['OUTPUT']

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Sample raster values
        alg_params = {
            'COLUMN_PREFIX': 'Slope_%class',
            'INPUT': outputs['ExtractFaibPlotsOfMerchantableSizeForEachSpecies']['OUTPUT'],
            'RASTERCOPY': outputs['Slope_crmclasses']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['SampleRasterValues'] = processing.run('native:rastersampling', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'LiDAR Metrics Extraction'

    def displayName(self):
        return 'LiDAR Metrics Extraction'

    def group(self):
        return 'EFI-CRM'

    def groupId(self):
        return 'EFI-CRM'

    def createInstance(self):
        return LidarMetricsExtraction()
