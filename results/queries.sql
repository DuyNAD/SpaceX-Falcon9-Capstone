-- launch_sites
SELECT DISTINCT LaunchSite FROM launches ORDER BY LaunchSite;

-- site_prefix
SELECT FlightNumber,Date,LaunchSite FROM launches WHERE LaunchSite LIKE 'CCA%' LIMIT 5;

-- payloads
SELECT LaunchSite,COUNT(*) AS launches,SUM(PayloadMass) AS total_kg,AVG(PayloadMass) AS mean_kg FROM launches GROUP BY LaunchSite;

-- success_rates
SELECT LaunchSite,COUNT(*) AS launches,SUM(Class) AS class1,ROUND(AVG(Class),4) AS class1_rate FROM launches GROUP BY LaunchSite ORDER BY class1_rate DESC;

-- first_rtls
SELECT MIN(Date) AS first_successful_RTLS FROM launches WHERE Outcome='True RTLS';

-- asds_payload
SELECT FlightNumber,Date,PayloadMass FROM launches WHERE Outcome='True ASDS' AND PayloadMass BETWEEN 4000 AND 6000;

-- outcome_counts
SELECT Outcome,COUNT(*) AS launches FROM launches GROUP BY Outcome ORDER BY launches DESC;

-- max_payload
SELECT FlightNumber,Date,Serial,PayloadMass FROM launches WHERE PayloadMass=(SELECT MAX(PayloadMass) FROM launches);

-- yearly
SELECT Year,COUNT(*) AS launches,SUM(Class) AS class1,ROUND(AVG(Class),4) AS class1_rate FROM launches GROUP BY Year ORDER BY Year;

-- time_window
SELECT Outcome,COUNT(*) AS launches FROM launches WHERE Date BETWEEN '2010-06-04' AND '2017-03-20' GROUP BY Outcome ORDER BY launches DESC;

-- 2015_asds_failures
SELECT Date,Serial,LaunchSite FROM launches WHERE Outcome='False ASDS' AND substr(Date,1,4)='2015';