install.packages('dplyr')
install.packages('tidyverse')
library(dplyr)
library(tidyverse)

# Task 1 
# Aggregate the countries in the original gapminder_dataset into regions based on the UN
# geoscheme
# (https://en.wikipedia.org/wiki/List_of_countries_by_United_Nations_geoscheme).


#Retrieved dataset for UN classification from UNSD Methodology (https://unstats.un.org/unsd/methodology/m49/overview/) 
#Renaming relevant columns of the data set for convenience and merging 

names(UNSD_Methodology)[names(UNSD_Methodology) == "Sub-region Name"] <- "subregion"
names(UNSD_Methodology)[names(UNSD_Methodology) == "Country or Area"] <- "country"

#Dropping irrelevant columns

UNSD_Methodology = subset (UNSD_Methodology, select = -c(1:5,7:8,10:15))

#changing country names to match with the given dataset

UNSD_Methodology[UNSD_Methodology == "Bolivia (Plurinational State of)"] <- "Bolivia"
UNSD_Methodology[UNSD_Methodology == "Bosnia and Herzegovina"] <- "Bosnia & Herzegovina"
UNSD_Methodology[UNSD_Methodology == "Congo"] <- "Congo - Brazzaville"
UNSD_Methodology[UNSD_Methodology == "Democratic Republic of the Congo"] <- "Congo - Kinshasa"
UNSD_Methodology[UNSD_Methodology == "China, Hong Kong Special Administrative Region"] <- "Hong Kong SAR China"
UNSD_Methodology[UNSD_Methodology == "Iran (Islamic Republic of)"] <- "Iran"
UNSD_Methodology[UNSD_Methodology == "Iran (Islamic Republic of)"] <- "Iran"
UNSD_Methodology[UNSD_Methodology == "Myanmar"] <- "Myanmar (Burma)"
UNSD_Methodology[UNSD_Methodology == "Sao Tome and Principe"] <- "São Tomé & Príncipe"
UNSD_Methodology[UNSD_Methodology == "Republic of Korea"] <- "South Korea"
UNSD_Methodology[UNSD_Methodology == "State of Palestine"] <- "Palestinian Territories"
UNSD_Methodology[UNSD_Methodology == "Syrian Arab Republic"] <- "Syria"
UNSD_Methodology[UNSD_Methodology == "Trinidad and Tobago"] <- "Trinidad & Tobago"
UNSD_Methodology[UNSD_Methodology == "United Kingdom of Great Britain and Northern Ireland"] <- "United Kingdom"
UNSD_Methodology[UNSD_Methodology == "United Republic of Tanzania"] <- "Tanzania"
UNSD_Methodology[UNSD_Methodology == "Viet Nam"] <- "Vietnam"
UNSD_Methodology[UNSD_Methodology == "United States of America"] <- "United States"

#merging with original dataset 

gapminder_dataset_1 <- merge(UNSD_Methodology, gapminder_dataset, by="country")

#Grouping the aggregate by region (continent), and subregion

by_continent <- gapminder_dataset_1 %>% group_by(continent)
by_subregion <- gapminder_dataset_1 %>% group_by(subregion)

# this allows to use some functions to get some insights on data, for example, which are the largest country groups 

by_continent %>% tally(sort=TRUE)
by_subregion %>% tally(sort=TRUE)

#The results tell us that around 40% of all observations come from Africa, 20% each from Americas, Asia, and Europe, and only 17 observations from Oceania
#Sub-region wise, observations from Sub-Saharan Africa and Latin America and the Caribbean are the dominant data in our set 

#Task 2 

#Create a new column “decade” which sorts years into their respective decades.

gapminder_dataset_2 <- gapminder_dataset_1 %>% 
  mutate(decade = case_when(year <= 1969 ~ "1960s", 
                            year <= 1979 ~ "1970s",
                            year <= 1989  ~ "1980s",
                            year <= 1999  ~ "1990s", 
                            year >= 2000  ~ "2000s"))

#a) Find the average life expectancy for each continent by decade. 

mean_table<-aggregate (gapminder_dataset_2$lifeExp, list(gapminder_dataset_2$continent,gapminder_dataset_2$decade), FUN=mean, sort=TRUE) 
names(mean_table)[names(mean_table) == "Group.1"] <- "Continent"
names(mean_table)[names(mean_table) == "Group.2"] <- "Decade"
names(mean_table)[names(mean_table) == "x"] <- "Average_Life_Expectancy"
mean_table<-mean_table[order(mean_table$Continent), ]

#Presenting data visually 
install.packages("ggplot2")
library(ggplot2)

ggplot(mean_table)+ geom_point(mapping = aes(x=Decade, y=Average_Life_Expectancy, group=Continent, color=Continent)) +
  geom_line(mapping = aes(x=Decade, y=Average_Life_Expectancy, group=Continent, color=Continent)) + ylab('Average Life Expectancy')

#b) Calculate average life expectancy for each country by decade. Create a scatter
#plot with GDP per capita on x-axis and life expectancy on the y-axis. Set the size
#of the points based on the size of the population and the color based on the sub
#region. 

#finding mean values per country per decate for average life expectancy, gdp, and population
mean_table_country_lifeexp<-aggregate (gapminder_dataset_2$lifeExp, list(gapminder_dataset_2$country,gapminder_dataset_2$decade), FUN=mean) 
mean_table_country_gdp<-aggregate (gapminder_dataset_2$gdpPercap, list(gapminder_dataset_2$country,gapminder_dataset_2$decade), FUN=mean) 
mean_table_country_pop<-aggregate (gapminder_dataset_2$pop, list(gapminder_dataset_2$country,gapminder_dataset_2$decade), FUN=mean) 

#renaming the columns
names(mean_table_country_lifeexp)[names(mean_table_country_lifeexp) == "Group.1"] <- "country"
names(mean_table_country_lifeexp)[names(mean_table_country_lifeexp) == "Group.2"] <- "decade"
names(mean_table_country_lifeexp)[names(mean_table_country_lifeexp) == "x"] <- "life_expectancy"

#merging together
mean_table_country_lifeexp <- cbind(mean_table_country_lifeexp, mean_table_country_gdp$x)
names(mean_table_country_lifeexp)[names(mean_table_country_lifeexp) == "mean_table_country_gdp$x"] <- "gdp_per_cap"
mean_table_country_lifeexp <- cbind(mean_table_country_lifeexp, mean_table_country_pop$x)
names(mean_table_country_lifeexp)[names(mean_table_country_lifeexp) == "mean_table_country_pop$x"] <- "population"

#including subregion column 
total_task2_df<-merge(mean_table_country_lifeexp,UNSD_Methodology, by="country")

#plotting 

#for convenience, creating new column with ranges for population
total_task2_df <- total_task2_df %>% 
  mutate(population_size = case_when(population <= 1000000 ~ "Less Than 1mln", 
                                     population <= 10000000 ~ "1mln-10mln",
                                     population <= 100000000  ~ "10mln-100mln",
                                     population <= 500000000  ~ "100mln-500mln", 
                                     population >= 500000000  ~ "Over 500mln"))
total_task2_df$population_size<-factor(total_task2_df$population_size, levels = c("Less Than 1mln", "1mln-10mln", "10mln-100mln", "100mln-500mln", "Over 500mln")) 

#Plotting
ggplot(total_task2_df, aes(x=gdp_per_cap, y=life_expectancy, size=population_size, colour=subregion, cex=2)) + geom_point()+xlab("GDP Per Capita")+ylab("Life Expectancy") + labs(fill = "Subregion") 

#Task3. Drop the life expectancy and continent column. Then, fill in the gaps for each
#country for both population and GDP per capita using the source of your choice

task3_df<- subset (gapminder_dataset_2, select = -c(3, 5))

#decades are also unnecessary 
task3_df<- subset (task3_df, select = -c(6))

#Inputting data for GDP per capita and population for years 1962-2007

install.packages("WDI")
library(WDI)

WDI_df<-WDI(
  country = "all",
  indicator = "NY.GDP.PCAP.KD",
  start = 1960,
  end = NULL,
  extra = FALSE,
  cache = NULL,
  latest = NULL,
  language = "en"
)

WDI_df_pop<-WDI(
  country = "all",
  indicator = "SP.POP.TOTL",
  start = 1960,
  end = NULL,
  extra = FALSE,
  cache = NULL,
  latest = NULL,
  language = "en"
)

WDI_df<-cbind(WDI_df, WDI_df_pop$SP.POP.TOTL)
names(WDI_df)[names(WDI_df) == "population"] <- "pop"
names(WDI_df)[names(WDI_df) == "NY.GDP.PCAP.KD"] <- "gdpPercap"
WDI_df<-subset(WDI_df, select= -c(2:3))

#Some country names do not match the original dataset. I might not be able to find all of them but I will change the ones I noticed 

WDI_df[WDI_df == "Bosnia and Herzegovina"] <- "Bosnia & Herzegovina"
WDI_df[WDI_df  == "Congo, Rep."] <- "Congo - Brazzaville"
WDI_df[WDI_df == "Congo, Dem. Rep."] <- "Congo - Kinshasa"
WDI_df[WDI_df == "Iran, Islamic Rep."] <- "Iran"
WDI_df[WDI_df == "Myanmar"] <- "Myanmar (Burma)"
WDI_df[WDI_df == "Sao Tome and Principe"] <- "São Tomé & Príncipe"
WDI_df[WDI_df == "Korea, Rep."] <- "South Korea"
WDI_df[WDI_df == "Syrian Arab Republic"] <- "Syria"
WDI_df[WDI_df == "Trinidad and Tobago"] <- "Trinidad & Tobago"

#ommitting observations with unknown variables 
WDI_df<-na.omit(WDI_df)

#merging the datasets

#including subregions classification in the WDI data 
WDI_df_subregions<-merge(WDI_df,UNSD_Methodology, by='country')

#merging the datasets
task3_final_df<-bind_rows(task3_df, WDI_df_subregions)

#Some rows duplicate and the data of WDI and the gapminder_dataset have different datapoints for GDP and population. 
#For that reason I will just use the WDI data instead for the following tasks as it provides with a bigger dataset and thus will produce more accurate analysis results 
task3_final_df<-WDI_df_subregions

#Exporting the dataset to Excel
install.packages('openxlsx')
library(openxlsx)
write.xlsx(task3_final_df, '/cloud/project/task3.xlsx')