% script radio_cum_time

% set up a quickie test array to confirm logic
delta_time_array = [2.1, 2.2, 2.4, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 600, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 1500, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 600, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 1500, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 600, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 1500, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, 2.1, 2.2, 300, ...
    2.1, 2.2, 300]; % sec
time_array = cumsum(delta_time_array);
number_of_times = numel(time_array);

% convert seconds to & from datenum for matlab time format.
datenum_to_sec = 24*60*60;
sec_to_datenum = 1/datenum_to_sec;
sec_to_hours = 1/(3600);

% this is a mock up the time of each pod message received
time_of_day_array = datenum(now) + time_array*sec_to_datenum;

% this is so I can make a pretty printout at the end - not needed
cum_radio_on_array = zeros(number_of_times,1);

%% code prototype here
% this constant is required
radio_active_time = 30; % sec

% initialize when pod pairs 
idx = 1;
last_radio_time = time_of_day_array(idx);
cum_radio_on = radio_active_time;

% each successive index mocks up when a message received from the pod
for idx = 2:number_of_times
    this_radio_time = time_of_day_array(idx);
    delta_time = (this_radio_time - last_radio_time)*datenum_to_sec;
    if delta_time > radio_active_time
        cum_radio_on = cum_radio_on + radio_active_time;
    else
        cum_radio_on = cum_radio_on + delta_time;
    end
    last_radio_time = this_radio_time;

    % next line is so I can make a pretty printout to verify logic
    cum_radio_on_array(idx) = cum_radio_on;
end
%% Print out results for logic can be confirmed
fprintf('Elapsed time of %8.2f hours\n', sec_to_hours * (time_array(end)-time_array(1)));
fprintf('Radio on for    %8.2f hours\n', sec_to_hours * cum_radio_on_array(end));
fprintf('Percentage      %8.1f%%\n', 100*cum_radio_on_array(end)/(time_array(end)-time_array(1)));
fprintf('DateTime, Cum(sec), Cum(hr)\n');
    
for idx = 1:12
    fprintf('%s, %8.2f, %8.2f\n', ...
        datestr(time_of_day_array(idx),'mm/dd/yy HH:MM:SS'), ...
        cum_radio_on_array(idx), sec_to_hours * cum_radio_on_array(idx));
end
fprintf('   . . . . \n');    
for idx = number_of_times-12:number_of_times
    fprintf('%s, %8.2f, %8.2f\n', ...
        datestr(time_of_day_array(idx),'mm/dd/yy HH:MM:SS'), ...
        cum_radio_on_array(idx), sec_to_hours * cum_radio_on_array(idx));
end

%% output of test
Elapsed time of     5.22 hours
Radio on for        0.46 hours
Percentage           8.7%
DateTime, Cum(sec), Cum(hr)
02/19/19 13:00:25,     0.00,     0.00
02/19/19 13:00:27,    32.20,     0.01
02/19/19 13:00:30,    34.60,     0.01
02/19/19 13:05:30,    64.60,     0.02
02/19/19 13:05:32,    66.70,     0.02
02/19/19 13:05:34,    68.90,     0.02
02/19/19 13:10:34,    98.90,     0.03
02/19/19 13:10:36,   101.00,     0.03
02/19/19 13:10:38,   103.20,     0.03
02/19/19 13:15:38,   133.20,     0.04
02/19/19 13:15:40,   135.30,     0.04
02/19/19 13:15:43,   137.50,     0.04
   . . . . 
02/19/19 17:53:30,  1505.20,     0.42
02/19/19 17:53:32,  1507.30,     0.42
02/19/19 17:53:35,  1509.50,     0.42
02/19/19 17:58:35,  1539.50,     0.43
02/19/19 17:58:37,  1541.60,     0.43
02/19/19 17:58:39,  1543.80,     0.43
02/19/19 18:03:39,  1573.80,     0.44
02/19/19 18:03:41,  1575.90,     0.44
02/19/19 18:03:43,  1578.10,     0.44
02/19/19 18:08:43,  1608.10,     0.45
02/19/19 18:08:45,  1610.20,     0.45
02/19/19 18:08:48,  1612.40,     0.45
02/19/19 18:13:48,  1642.40,     0.46

