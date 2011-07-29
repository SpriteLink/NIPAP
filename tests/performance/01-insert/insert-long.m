d0 = load('data.insert-4610-24s');
plot(d0(:,1), d0(:,2), 'r');
xlabel('Prefix number');
ylabel('Insert time [s]');
legend('after ip4r');
title('Prefix insertion time');
print('plot-4610-24s.png','-dpng','-S640,480');

