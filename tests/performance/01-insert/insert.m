
% 

% plot first graph - insertion time before optimization
d0 = load('data.insert-start');
plot(d0(:,1), d0(:,2), 'r');
legend('baseline');
title('Prefix insertion time');
xlabel('Prefix number');
ylabel('Insert time [s]');
print('plot-before.png','-dpng','-S640,480');

hold('on');
% insertion time after optimization, retaining the old plot (ie before
% optimization) and printing a combined graph
d1 = load('data.insert-after-ip4r');
plot(d1(:,1), d1(:,2), 'b');
legend('before ip4r', 'after ip4r');
xlabel('Prefix number');
ylabel('Insert time [s]');
print('plot-before-and-after.png','-dpng','-S640,480');

% plot our long running test in a new graph
hold('off');
d2 = load('data.insert-4610-24s');
plot(d2(:,1), d2(:,2), 'r');
legend('after ip4r');
title('Prefix insertion time');
xlabel('Prefix number');
ylabel('Insert time [s]');
print('plot-after-4610-24s.png','-dpng','-S640,480');

