# -*- coding: utf-8 -*-
"""
Created on Thu Oct 12 17:01:34 2023

This code checks quality of EORA datasets by comparing it to the World Bank Data
The year checked is 2015 at basic prices, for countries wih standard sector classification

@author: ep
"""

import csv
import pandas as pd
import numpy as np
from pandas import Series, DataFrame
import os
from statistics import mean 
import matplotlib.pyplot as plt
import seaborn as sns

'''Function to read in EORA tables of Basic Prices'''

def read_data():
   
    
    input_path = "Raw Data"
    output_path = "Processed Data"
    file_list_full = os.listdir(input_path)
    
    country_codes = pd.read_excel('country_codes.xlsx')
    country_codes_list = country_codes['Code'].tolist()
    
    files_list_final = []
    for file_name in file_list_full:
        if 'BasicPrice' in file_name:
            if file_name.split('_')[1] in country_codes_list:
               files_list_final.append(file_name)
    
    out_files = []
    for i in files_list_final:
       out_files.append('{fname}.csv'.format(fname = i[:-4]))
    
    for i, o in zip(files_list_final, out_files):
        io = pd.read_csv(os.path.join(input_path, i), sep='\t', header=None, on_bad_lines='skip', nrows = 226)
        io.to_csv(os.path.join(output_path, o), index=False, header=False)
    
    EORA_data = {}
    for o in out_files:
        EORA_data[o.split('_')[1]] = pd.read_csv(os.path.join(output_path, o))
        
    return EORA_data    
     
if __name__ == '__main__':
    
    #%%
    
    '''    
    Reading in the EORA data
    '''
   
    EORA_data = read_data()
   
    #Tidyig up 
    
    #Changing to float type will be useful later 
    
    for country, table in EORA_data.items():
      EORA_data[country].iloc[3:, 4:] = EORA_data[country].iloc[3:, 4:].astype(float)
    
    # Extract trade data
    imports = {}
    for country, table in EORA_data.items():
        imports[country] = table.iloc[35:(35+190), 0:(4+32)]
    
    exports = {}
    for country, table in EORA_data.items():
        exports[country] = table.iloc[0:36, 36:(36+190)]
    
    #Sum imports
    aggregate_imports = {}
    for country, imp_table in imports.items():
        aggregate_imports[country] = imp_table.sum(axis=0)

    #Sum exports
    aggregate_exports = {}
    for country, exp_table in exports.items():
        aggregate_exports[country] = exp_table.sum(axis=1)

    #Keeping relative table rows only   

    EORA_data1 = {}
    for country, table in EORA_data.items():
          EORA_data1[country] = EORA_data[country].iloc[0:35, 0:36]
   
    #Adding aggregate imports back
    for country, table in EORA_data1.items():
         EORA_data1[country].loc[len(EORA_data1[country])] = aggregate_imports[country]
    
    for country, table in EORA_data1.items():
        EORA_data1[country].iloc[35, 0:3] =  EORA_data1[country].iloc[34, 0:3]
        EORA_data1[country].iloc[35, 3] = 'Imports'
    
    #Adding aggregate exports back 
    for country, table in EORA_data1.items():
         EORA_data1[country]['Exports'] = aggregate_exports[country].values
             
    for country, table in EORA_data1.items():
          EORA_data1[country].iloc [0:1, 36] =  EORA_data1[country].iloc[0:1, 35]
          EORA_data1[country].iloc[2, 36] = 'Exports'  

    #%%
    ''' 
    READING IN WORLD BANK DATA
    
    Meta Data: 
        
        BASE YEAR
        National accounts base year differs throughout the countries 
        
        DATA SOURCE
        World Bank national accounts data and OECD National Accounts data files
        
        PRICES
        Total GDP is measured at purchasers prices. Value added by industry is normally measured at basic prices. 
        
        AGRICULTURE
        Large share of agriculture is unreported - in the World Bank data, which uses national accounts,
        it is estimated indirectly, using estimates of inputs, yields, and area under cultivation. 
        
    '''

    #Reading in the csv file 
    World_Bank_data = pd.read_csv('World_Bank_Data.csv', delimiter=',')
    World_Bank_data = World_Bank_data.replace('..', 0)
    World_Bank_data.loc[:, '2015 [YR2015]'] = World_Bank_data.loc[:, '2015 [YR2015]'].astype(float)

    #Tidying up 

    #Separating data by country
    
    #Only keeping countries that overlap in EORA and World Bank 
    country_list_EORA = list(EORA_data1.keys())
    country_list_WB = list(World_Bank_data['Country Code'])
    country_list_EORA = [x for x in country_list_EORA if x in country_list_WB]
   
    WB_bycountry = {}
    
    for country in country_list_EORA:     
         WB_bycountry[country] = World_Bank_data[World_Bank_data['Country Code'] == country]

    
    #Calculating shares 
    Shares_bycountry = {}
    for country, table in WB_bycountry.items():
        Shares_bycountry[country] = [WB_bycountry[country].iloc[0,4]/WB_bycountry[country].iloc[4,4], 
                                         WB_bycountry[country].iloc[1,4]/WB_bycountry[country].iloc[4,4],
                                         WB_bycountry[country].iloc[2,4]/WB_bycountry[country].iloc[4,4],
                                         WB_bycountry[country].iloc[3,4]/WB_bycountry[country].iloc[4,4],
                                         WB_bycountry[country].iloc[4,4]/WB_bycountry[country].iloc[4,4]] 
    #Adding shares back as columns
    
    for country, table in WB_bycountry.items(): 
        WB_bycountry[country]['Share of GDP'] = Shares_bycountry[country]
      
    #deflating the shares    
    deflator = {}
    for country, table in WB_bycountry.items():
        deflator[country] = WB_bycountry[country].iloc[0:2, 5].sum() + WB_bycountry[country].iloc[3, 5].sum()
        
    for country, table in WB_bycountry.items(): 
         WB_bycountry[country]['Deflated Share'] = WB_bycountry[country]['Share of GDP']*deflator[country]
    
    #%%
    '''
    Grouping industries by sectors in EORA data, calculating shares of GVA  
    Industries 'Others' and 'Re-Exports and Re-Imports' not accounted for
    '''
    #Creating lists of sector classifications 
    
    industries_list = EORA_data['ABW'].iloc[3:29, 3].tolist()
    Agriculture = industries_list[0:2]
    Industry = industries_list[2:14] 
    Manufacturing = industries_list[3:11]
    Services = industries_list[14:24]
      
    EORA_data2 = {}
    for country, table in EORA_data1.items():
      if country in country_list_EORA:
         EORA_data2[country] = EORA_data1[country]
    
    for country, table in EORA_data2.items():
         EORA_data2[country] = EORA_data2[country].append(EORA_data2[country].iloc[29:35].sum(), ignore_index = True)
         EORA_data2[country].iloc[36, 3] = 'Total GVA'
         EORA_data2[country].iloc[36, 0:3] = ''
    
    EORA_agri = {}
    for country, table in EORA_data2.items():
        EORA_agri[country] = EORA_data2[country].loc[:, EORA_data2[country].isin(Agriculture).any()]
        
    EORA_ind = {}
    for country, table in EORA_data2.items():
        EORA_ind[country] = EORA_data2[country].loc[:, EORA_data2[country].isin(Industry).any()]
    
    EORA_man = {}
    for country, table in EORA_data2.items():
        EORA_man[country] = EORA_data2[country].loc[:, EORA_data2[country].isin(Manufacturing).any()]
        
    EORA_ser = {}
    for country, table in EORA_data2.items():
        EORA_ser[country] = EORA_data2[country].loc[:, EORA_data2[country].isin(Services).any()]
 
    EORA_data_bysector = {"Agriculture": EORA_agri, "Industry": EORA_ind, "Manufacturing": EORA_man, "Services": EORA_ser}

    #Finding the share of sector's GVA as total GVA 
    
    EORA_shares_agri = {}
    for country, table in EORA_data_bysector['Agriculture'].items():
        for country, table in EORA_data2.items():
            EORA_shares_agri[country] = EORA_data_bysector['Agriculture'][country].iloc[36, 1:].sum()/EORA_data2[country].iloc[36, 4:29].sum()
       
    EORA_shares_ind = {}
    for country, table in EORA_data_bysector['Industry'].items():
        for country, table in EORA_data2.items():
            EORA_shares_ind[country] = EORA_data_bysector['Industry'][country].iloc[36, 1:].sum()/EORA_data2[country].iloc[36, 4:29].sum()
        
                
    EORA_shares_man = {}
    for country, table in EORA_data_bysector['Manufacturing'].items():
        for country, table in EORA_data2.items():
            EORA_shares_man[country] = EORA_data_bysector['Manufacturing'][country].iloc[36, 1:].sum()/EORA_data2[country].iloc[36, 4:29].sum()
        
    EORA_shares_ser = {}
    for country, table in EORA_data_bysector['Services'].items():
        for country, table in EORA_data2.items():
            EORA_shares_ser[country] = EORA_data_bysector['Services'][country].iloc[36, 1:].sum()/EORA_data2[country].iloc[36, 4:29].sum()
          
    #Creating a dictionary with all the shares
     
    final_dataframe = {}
    final_dataframe = WB_bycountry
    
    for country, table in final_dataframe.items():
        final_dataframe[country]['EORA Share'] = [ EORA_shares_agri[country], EORA_shares_ind[country], EORA_shares_man[country], 
                                                  EORA_shares_ser[country], EORA_data2[country].iloc[36, 4:29].sum()/final_dataframe[country].iloc[4, 4]]         
    
    final_df = {k: v for k, v in final_dataframe.items() if v.notna().all().all()} 
    
    #%%
    '''
    Comparison of World Bank and EORA data and presenting 
    '''
    #finding the difference
        
    #turning everything to percentage terms
    for country, table in final_df.items():
        final_df[country] = final_df[country].rename(columns = {'Deflated Share': 'Deflated Share (%)', 'EORA Share' : 'EORA Share (%)'})
        final_df[country]['Deflated Share (%)'] = final_df[country]['Deflated Share (%)'].mul(100)
        final_df[country]['EORA Share (%)'] = final_df[country]['EORA Share (%)'].mul(100)
    
    for country, table in final_df.items():
        final_df[country]['Difference between WB and EORA'] = (final_df[country]['Deflated Share (%)'] - final_df[country]['EORA Share (%)'])
    
    
    for country, table in final_df.items():
        final_df[country]['ABS Difference between WB and EORA'] = abs(final_df[country]['Deflated Share (%)'] - final_df[country]['EORA Share (%)'])
   
    shares_diff_agri_abs = []
    for country, table in final_df.items():   
        shares_diff_agri_abs.append(final_df[country].iloc[0,9])
    agri_mean = mean(shares_diff_agri_abs)

    shares_diff_ind_abs = []
    for country, table in final_df.items():   
        shares_diff_ind_abs.append(final_df[country].iloc[1,9])
    ind_mean = mean(shares_diff_ind_abs)

    shares_diff_man_abs = []
    for country, table in final_df.items():   
        shares_diff_man_abs.append(final_df[country].iloc[2,9])
    man_mean = mean(shares_diff_man_abs)

    shares_diff_ser_abs = []
    for country, table in final_df.items():   
        shares_diff_ser_abs.append(final_df[country].iloc[3,9]) 
    ser_mean = mean(shares_diff_ser_abs)
    
    #Plotting the means 
    
    xpoints = ['Agriculture', 'Industry', 'Manufacturing', 'Services']
    ypoints = [agri_mean, ind_mean, man_mean, ser_mean]
    plt.bar(xpoints, ypoints) 
    plt.title('Absolute average difference between percentages of GVA of World Bank and EORA data by sector')
    
    #Plotting scatter plot for each data point and each sector 
    
    shares_diff_agri = []
    for country, table in final_df.items():   
       shares_diff_agri.append(final_df[country].iloc[0,8])

    shares_diff_ind = []
    for country, table in final_df.items():   
       shares_diff_ind.append(final_df[country].iloc[1,8])

    shares_diff_man = []
    for country, table in final_df.items():   
       shares_diff_man.append(final_df[country].iloc[2,8])

    shares_diff_ser = []
    for country, table in final_df.items():   
       shares_diff_ser.append(final_df[country].iloc[3,8]) 
       
    scatter_data = {'Agriculture' : shares_diff_agri, 'Industry' : shares_diff_ind, 'Manufacturing' : shares_diff_man, 'Services': shares_diff_ser}  
    scatter_dataframe = pd.DataFrame.from_dict(scatter_data)
    scatter_df = pd.DataFrame([(colname, scatter_dataframe[colname][i]) for i in range(len(scatter_dataframe)) for colname in scatter_dataframe.columns], 
                 columns=['Sector', 'Difference of shares of GVA between EORA and WB data'])
    sns.stripplot(x = 'Sector', y='Difference of shares of GVA between EORA and WB data', data=scatter_df)
    
  
    #By income group 
    country_class = pd.read_excel('country_class.xlsx')
    income_group_dict = dict(zip(country_class['Country code'], country_class['Class']))
    country_list = list(final_df.keys())
   
    income_group_dict1 ={}
    for key in income_group_dict:
        if key in country_list:
            income_group_dict1[key] = income_group_dict[key]
            
    income_groups = ['H', 'UM', 'LM', 'l']
   
    H = []
    for key, value in income_group_dict1.items(): 
        if income_group_dict1[key] == 'H':
            H.append(key)
            
    UM = []
    for key, value in income_group_dict1.items(): 
        if income_group_dict1[key] == 'UM':
            UM.append(key)
    LM = []
    for key, value in income_group_dict1.items(): 
        if income_group_dict1[key] == 'LM':
            LM.append(key)
    L = []
    for key, value in income_group_dict1.items(): 
        if income_group_dict1[key] == 'L':
            L.append(key)
       
    H_dict = {country: final_df[country] for country in final_df.keys() if country in H}
    UM_dict = {country: final_df[country] for country in final_df.keys() if country in UM}
    LM_dict = {country: final_df[country] for country in final_df.keys() if country in LM}
    L_dict = {country: final_df[country] for country in final_df.keys() if country in L}

    by_income_group = {'H': H_dict, 'UM' : UM_dict, 'LM' : LM_dict, 'L': L_dict}
  
    #High income
    shares_diff_agri_H = []
    for country, table in H_dict.items():   
       shares_diff_agri_H.append(H_dict[country].iloc[0,8])

    shares_diff_ind_H = []
    for country, table in H_dict.items():  
       shares_diff_ind_H.append(H_dict[country].iloc[1,8])

    shares_diff_man_H = []
    for country, table in H_dict.items(): 
       shares_diff_man_H.append(H_dict[country].iloc[2,8])

    shares_diff_ser_H = []
    for country, table in H_dict.items():   
       shares_diff_ser_H.append(H_dict[country].iloc[3,8]) 
       
    scatter_data_H = {'Agriculture' : shares_diff_agri_H, 'Industry' : shares_diff_ind_H, 'Manufacturing' : shares_diff_man_H, 'Services': shares_diff_ser_H}  
    scatter_dataframe_H = pd.DataFrame.from_dict(scatter_data_H)
    scatter_df_H = pd.DataFrame([(colname, scatter_dataframe_H[colname][i]) for i in range(len(scatter_dataframe_H)) for colname in scatter_dataframe_H.columns], 
              columns=['Sector', 'Difference of shares of GVA between WB and EORA data'])
    sns.stripplot(x = 'Sector', y='Difference of shares of GVA between WB and EORA data', data=scatter_df_H).set(title='High Income')
       
    #UM income
    shares_diff_agri_UM = []
    for country, table in UM_dict.items():   
       shares_diff_agri_UM.append(UM_dict[country].iloc[0,8])

    shares_diff_ind_UM = []
    for country, table in UM_dict.items():  
       shares_diff_ind_UM.append(UM_dict[country].iloc[1,8])

    shares_diff_man_UM = []
    for country, table in UM_dict.items(): 
       shares_diff_man_UM.append(UM_dict[country].iloc[2,8])

    shares_diff_ser_UM = []
    for country, table in UM_dict.items():   
       shares_diff_ser_UM.append(UM_dict[country].iloc[3,8]) 
       
    scatter_data_UM = {'Agriculture' : shares_diff_agri_UM, 'Industry' : shares_diff_ind_UM, 'Manufacturing' : shares_diff_man_UM, 'Services': shares_diff_ser_UM}  
    scatter_dataframe_UM = pd.DataFrame.from_dict(scatter_data_UM)
    scatter_df_UM = pd.DataFrame([(colname, scatter_dataframe_UM[colname][i]) for i in range(len(scatter_dataframe_UM)) for colname in scatter_dataframe_UM.columns], 
              columns=['Sector', 'Difference of shares of GVA between WB and EORA data'])
    sns.stripplot(x = 'Sector', y='Difference of shares of GVA between WB and EORA data', data=scatter_df_UM).set(title='Upper Middle Income')
       
       
    #LM income 
    
    shares_diff_agri_LM = []
    for country, table in LM_dict.items():   
       shares_diff_agri_LM.append(LM_dict[country].iloc[0,8])

    shares_diff_ind_LM = []
    for country, table in LM_dict.items():  
       shares_diff_ind_LM.append(LM_dict[country].iloc[1,8])

    shares_diff_man_LM = []
    for country, table in LM_dict.items(): 
       shares_diff_man_LM.append(LM_dict[country].iloc[2,8])

    shares_diff_ser_LM = []
    for country, table in LM_dict.items():   
       shares_diff_ser_LM.append(LM_dict[country].iloc[3,8]) 
      
    scatter_data_LM = {'Agriculture' : shares_diff_agri_LM, 'Industry' : shares_diff_ind_LM, 'Manufacturing' : shares_diff_man_LM, 'Services': shares_diff_ser_LM}  
    scatter_dataframe_LM = pd.DataFrame.from_dict(scatter_data_LM)
    scatter_df_LM = pd.DataFrame([(colname, scatter_dataframe_LM[colname][i]) for i in range(len(scatter_dataframe_LM)) for colname in scatter_dataframe_LM.columns], 
               columns=['Sector', 'Difference of shares of GVA between WB and EORA data'])
    sns.stripplot(x = 'Sector', y='Difference of shares of GVA between WB and EORA data', data=scatter_df_LM).set(title='Lower Middle Income')
         
      
    #L income 
    
    shares_diff_agri_L = []
    for country, table in L_dict.items():   
       shares_diff_agri_L.append(L_dict[country].iloc[0,8])

    shares_diff_ind_L = []
    for country, table in L_dict.items():  
       shares_diff_ind_L.append(L_dict[country].iloc[1,8])

    shares_diff_man_L = []
    for country, table in L_dict.items(): 
       shares_diff_man_L.append(L_dict[country].iloc[2,8])

    shares_diff_ser_L = []
    for country, table in L_dict.items():   
       shares_diff_ser_L.append(L_dict[country].iloc[3,8]) 
    
    scatter_data_L = {'Agriculture' : shares_diff_agri_L, 'Industry' : shares_diff_ind_L, 'Manufacturing' : shares_diff_man_L, 'Services': shares_diff_ser_L}  
    scatter_dataframe_L = pd.DataFrame.from_dict(scatter_data_L)
    scatter_df_L = pd.DataFrame([(colname, scatter_dataframe_L[colname][i]) for i in range(len(scatter_dataframe_L)) for colname in scatter_dataframe_L.columns], 
           columns=['Sector', 'Difference of shares of GVA between WB and EORA data'])
    sns.stripplot(x = 'Sector', y='Difference of shares of GVA between WB and EORA data', data=scatter_df_L).set(title='Low Income')
  #%%
    '''
    Comparing final expenditures as share of GDP
    '''
    #Importing World Bank data
    #Reading in the csv file 
    WB_final_expenditure = pd.read_csv('WB_fe.csv', delimiter=',')
    WB_final_expenditure.replace('..', np.nan, inplace=True)
    WB_final_expenditure.loc[:, '2015 [YR2015]'] = WB_final_expenditure.loc[:, '2015 [YR2015]'].astype(float)

    #Tidying up 

    #Separating data by country
    
    #Only keeping countries that overlap in EORA and World Bank 
    country_list_WB_fe = list(WB_final_expenditure['Country Code'])
    country_list_EORA_fe = [x for x in country_list_EORA if x in country_list_WB_fe]
   
    WB_bycountry_fe = {}
    
    for country in country_list_EORA_fe:     
         WB_bycountry_fe[country] =  WB_final_expenditure[ WB_final_expenditure['Country Code'] == country]

    WB_bycountry_fe  = {k: v for k, v in  WB_bycountry_fe.items() if v.notna().all().all()} 
    
    
    #Calculating the shares
    Shares_bycountry_fe = {}
    for country, table in WB_bycountry_fe.items():
        Shares_bycountry_fe[country] = [WB_bycountry_fe[country].iloc[0,4]/WB_bycountry_fe[country].iloc[3,4], 
                                         WB_bycountry_fe[country].iloc[1,4]/WB_bycountry_fe[country].iloc[3,4],
                                         WB_bycountry_fe[country].iloc[2,4]/WB_bycountry_fe[country].iloc[3,4],
                                         WB_bycountry_fe[country].iloc[3,4]/WB_bycountry_fe[country].iloc[3,4]]
                                         
    #Adding shares back as columns
    
    for country, table in WB_bycountry_fe.items(): 
        WB_bycountry_fe[country]['Share of GDP'] = Shares_bycountry_fe[country]
      
   #%%
   
    '''
    Finding shares for EORA data. 
    Process: find GDP by adding final expenditure, and net exports; Find shares of the same components as WB 
    '''
   
    
   #Finding net exports
   
    total_exports = {}
    for country, exports in aggregate_exports.items():
        total_exports[country] = aggregate_exports[country][3:].sum()
        
    total_imports = {}
    for country, imports in aggregate_imports.items():
        total_imports[country] = aggregate_imports[country][4:].sum()
        
    net_exports = {}
    for country in country_list_EORA:
        net_exports[country] = total_exports[country] - total_imports[country]
        
   #Calculating GDP expenditure approach from EORA dataframe
   
    gdp_by_country_EORA = {}
    for country, table in EORA_data2.items():
        gdp_by_country_EORA[country] = (EORA_data2[country].iloc[3:29, 30:36].values.sum() + 
                                        net_exports[country])
   
   #Household and NPISH 

    share_household_and_NPISH = {}
    for country, table in EORA_data2.items():
        share_household_and_NPISH[country] =  ((EORA_data2[country].iloc[3:29, 30].sum() + 
                                              EORA_data2[country].iloc[3:29, 31].sum())/
                                              gdp_by_country_EORA[country])

   
   #Government
   
    share_government = {}
    for country, table in EORA_data2.items():
        share_government[country] =  (EORA_data2[country].iloc[3:29, 32].sum()/
                                              gdp_by_country_EORA[country])
   
   #Investment 
   
    share_investment = {}
    for country, table in EORA_data2.items():
        share_investment[country] =  ((EORA_data2[country].iloc[3:29, 33].sum() +
                                       EORA_data2[country].iloc[3:29, 34].sum() +
                                             EORA_data2[country].iloc[3:29, 35].sum())/
                                             gdp_by_country_EORA[country])
 
   #Adding to World Bank data to compare
    fe_final_dataframe = {}
    fe_final_dataframe = WB_bycountry_fe
 
    for country, table in fe_final_dataframe.items():
        fe_final_dataframe[country]['EORA Share'] = [share_household_and_NPISH[country], share_investment[country], share_government[country], 
                                               gdp_by_country_EORA[country]/fe_final_dataframe[country].iloc[3, 4]]         
 
    for country, table in fe_final_dataframe.items():
        fe_final_dataframe[country]['ABS Difference between WB and EORA'] = abs(fe_final_dataframe[country]['Share of GDP'] - fe_final_dataframe[country]['EORA Share'])
   
   #Calculatign difference means
    shares_diff_household_abs = []
    for country, table in fe_final_dataframe.items():   
        shares_diff_household_abs.append(fe_final_dataframe[country].iloc[0,7])
    household_mean = mean(shares_diff_household_abs)

    shares_diff_investment_abs = []
    for country, table in fe_final_dataframe.items():   
       shares_diff_investment_abs.append(fe_final_dataframe[country].iloc[1,7])
    investment_mean = mean(shares_diff_investment_abs)

    shares_diff_government_abs = []
    for country, table in fe_final_dataframe.items():   
        shares_diff_government_abs.append(fe_final_dataframe[country].iloc[2, 7])
    government_mean = mean(shares_diff_government_abs)

   
    #Plotting the means 
    
    xpoints = ['Household and NPISH', 'Investment', 'Governmnet']
    ypoints = [household_mean, investment_mean, government_mean]
    plt.bar(xpoints, ypoints) 
    plt.title('Absolute average difference between shares of GDP of World Bank and EORA')
     
    #Plotting level differences
    
    for country, table in fe_final_dataframe.items():
        fe_final_dataframe[country]['Difference between WB and EORA'] = (fe_final_dataframe[country]['Share of GDP'] - fe_final_dataframe[country]['EORA Share'])
    
    shares_diff_household = []
    for country, table in fe_final_dataframe.items():   
       shares_diff_household.append(fe_final_dataframe[country].iloc[0,8])

    shares_diff_investment = []
    for country, table in fe_final_dataframe.items():   
        shares_diff_investment.append(fe_final_dataframe[country].iloc[1,8])

    shares_diff_government = []
    for country, table in fe_final_dataframe.items():   
       shares_diff_government.append(fe_final_dataframe[country].iloc[2,8])
       
    scatter_data_fe = {'Household' : shares_diff_household, 'Investment' : shares_diff_investment, 'Governmnet' : shares_diff_government}  
    scatter_dataframe_fe = pd.DataFrame.from_dict(scatter_data_fe)
    scatter_df_fe = pd.DataFrame([(colname, scatter_dataframe_fe[colname][i]) for i in range(len(scatter_dataframe_fe)) for colname in scatter_dataframe_fe.columns], 
                 columns=['Final Expenditure', 'Difference of shares of GDP between WB and EORA data'])
    sns.stripplot(x = 'Final Expenditure', y='Difference of shares of GDP between WB and EORA data', data=scatter_df_fe)
    
    #By income group 
       
    fe_H_dict = {country: fe_final_dataframe[country] for country in fe_final_dataframe.keys() if country in H}
    fe_UM_dict = {country: fe_final_dataframe[country] for country in fe_final_dataframe.keys() if country in UM}
    fe_LM_dict = {country: fe_final_dataframe[country] for country in fe_final_dataframe.keys() if country in LM}
    fe_L_dict = {country: fe_final_dataframe[country] for country in fe_final_dataframe.keys() if country in L}
  
    #High income
    shares_diff_household_H = []
    for country, table in fe_H_dict.items():   
       shares_diff_household_H.append(fe_H_dict[country].iloc[0,8])

    shares_diff_investment_H = []
    for country, table in fe_H_dict.items():  
       shares_diff_investment_H.append(fe_H_dict[country].iloc[1,8])

    shares_diff_government_H = []
    for country, table in fe_H_dict.items(): 
       shares_diff_government_H.append(fe_H_dict[country].iloc[2,8])
       
    scatter_data_fe_H = {'Household' : shares_diff_household_H, 'Investment' : shares_diff_investment_H, 'Governmnet' : shares_diff_government_H}  
    scatter_dataframe_fe_H = pd.DataFrame.from_dict(scatter_data_fe_H)
    scatter_df_fe_H = pd.DataFrame([(colname, scatter_dataframe_fe_H[colname][i]) for i in range(len(scatter_dataframe_fe_H)) for colname in scatter_dataframe_fe_H.columns], 
                 columns=['Final Expenditure', 'Difference of shares of GDP between WB and EORA data'])
    sns.stripplot(x = 'Final Expenditure', y='Difference of shares of GDP between WB and EORA data', data=scatter_df_fe_H).set(title='High Income')
       
    #UM income
    shares_diff_household_UM = []
    for country, table in fe_UM_dict.items():   
      shares_diff_household_UM.append(fe_UM_dict[country].iloc[0,8])

    shares_diff_investment_UM = []
    for country, table in fe_UM_dict.items():  
      shares_diff_investment_UM.append(fe_UM_dict[country].iloc[1,8])

    shares_diff_government_UM = []
    for country, table in fe_UM_dict.items(): 
      shares_diff_government_UM.append(fe_UM_dict[country].iloc[2,8])
      
    scatter_data_fe_UM = {'Household' : shares_diff_household_UM, 'Investment' : shares_diff_investment_UM, 'Governmnet' : shares_diff_government_UM}  
    scatter_dataframe_fe_UM = pd.DataFrame.from_dict(scatter_data_fe_UM)
    scatter_df_fe_UM = pd.DataFrame([(colname, scatter_dataframe_fe_UM[colname][i]) for i in range(len(scatter_dataframe_fe_UM)) for colname in scatter_dataframe_fe_UM.columns], 
                columns=['Final Expenditure', 'Difference of shares of GDP between WB and EORA data'])
    sns.stripplot(x = 'Final Expenditure', y='Difference of shares of GDP between WB and EORA data', data=scatter_df_fe_UM).set(title='Upper Middle Income')
      
    #LM income 
    
    shares_diff_household_LM = []
    for country, table in fe_LM_dict.items():   
      shares_diff_household_LM.append(fe_LM_dict[country].iloc[0,8])

    shares_diff_investment_LM = []
    for country, table in fe_LM_dict.items():  
      shares_diff_investment_LM.append(fe_LM_dict[country].iloc[1,8])

    shares_diff_government_LM = []
    for country, table in fe_LM_dict.items(): 
      shares_diff_government_LM.append(fe_LM_dict[country].iloc[2,8])
      
    scatter_data_fe_LM = {'Household' : shares_diff_household_LM, 'Investment' : shares_diff_investment_LM, 'Governmnet' : shares_diff_government_LM}  
    scatter_dataframe_fe_LM = pd.DataFrame.from_dict(scatter_data_fe_LM)
    scatter_df_fe_LM = pd.DataFrame([(colname, scatter_dataframe_fe_LM[colname][i]) for i in range(len(scatter_dataframe_fe_LM)) for colname in scatter_dataframe_fe_LM.columns], 
                columns=['Final Expenditure', 'Difference of shares of GDP between WB and EORA data'])
    sns.stripplot(x = 'Final Expenditure', y='Difference of shares of GDP between WB and EORA data', data=scatter_df_fe_LM).set(title='Lower Middle Income')
          
      
    #L income 
    
    shares_diff_household_L = []
    for country, table in fe_L_dict.items():   
      shares_diff_household_L.append(fe_L_dict[country].iloc[0,8])

    shares_diff_investment_L = []
    for country, table in fe_L_dict.items():  
      shares_diff_investment_L.append(fe_L_dict[country].iloc[1,8])

    shares_diff_government_L = []
    for country, table in fe_L_dict.items(): 
      shares_diff_government_L.append(fe_L_dict[country].iloc[2,8])
      
    scatter_data_fe_L = {'Household' : shares_diff_household_L, 'Investment' : shares_diff_investment_L, 'Governmnet' : shares_diff_government_L}  
    scatter_dataframe_fe_L = pd.DataFrame.from_dict(scatter_data_fe_L)
    scatter_df_fe_L = pd.DataFrame([(colname, scatter_dataframe_fe_L[colname][i]) for i in range(len(scatter_dataframe_fe_L)) for colname in scatter_dataframe_fe_L.columns], 
                columns=['Final Expenditure', 'Difference of shares of GDP between WB and EORA data'])
    sns.stripplot(x = 'Final Expenditure', y='Difference of shares of GDP between WB and EORA data', data=scatter_df_fe_UM).set(title='Lower Income')
      