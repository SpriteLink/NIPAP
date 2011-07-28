d0 = load('data.insert-start');
d1 = load('data.insert-after-ip4r');
plot(d0(:,1), d0(:,2), 'r');
hold('on');
plot(d1(:,1), d1(:,2), 'b');
xlabel('Prefix number');
ylabel('Insert time [s]');
legend('before ip4r', 'after ip4r');
title('Prefix insertion time');
print('plot.png','-dpng','-S640,480');

