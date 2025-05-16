function basinplot;

fclose all;
close all;
clc;

% Print?
printen      = 1;

% Geometry
B            =  550;
L            = 1800;

% Parameters
ms           =   12;
fs           =   12;
lw1          =    3;
lw2          =    1;
cl           =  0.5;
fac          =  1.15;

% Plot lines
line([0 L],[0 0],'linewidth',lw1,'color','k');
line([0 L],[B B],'linewidth',lw1,'color','k');
line([0 0],[0 B],'linewidth',lw1,'color','k');
line([L L],[0 B],'linewidth',lw2,'color','k','linestyle','--');

% Beautify
daspect([1 1 1]);
frac         =    10;
xlim([fac*(0-frac) fac*(L+frac)]);
ylim([fac*(0-frac) fac*(B+frac)]);
set(gca,'xtick',[0:B:L]);
set(gca,'ytick',[0:B:B]);
ax           = axis;
ap           = get(gca,'Position');
set(gca,'xticklabel',[{'0'} {'B'} {'2B'} {'3B'}]);
set(gca,'yticklabel',[{'0'} {'B'}]);
set(gca,'fontsize',fs);

% Incoming Kelvin arrow
box off;
x            = [ 900 1300];
y            = [ 450  450];
dx           =  50;
dy           =  25;
line(x,y,'linewidth',lw2,'color',[cl cl cl]);
line([x(1) x(1)+dx],[y(1) y(1)-dy],'linewidth',lw2,'color',[cl cl cl]);
line([x(1) x(1)+dx],[y(1) y(1)+dy],'linewidth',lw2,'color',[cl cl cl]);

% Outgoing Kelvin arrow
x            = [ 900 1300];
y            = [ 100  100];
dx           =  50;
dy           =  25;
line(x,y,'linewidth',lw2,'color',[cl cl cl]);
line([x(2) x(2)-dx],[y(2) y(2)-dy],'linewidth',lw2,'color',[cl cl cl]);
line([x(2) x(2)-dx],[y(2) y(2)+dy],'linewidth',lw2,'color',[cl cl cl]);

% Poincare arrow
x            = [ 100  100];
y            = [ 450  100];
dx           =  25;
dy           =  50;
line(x,y,'linewidth',lw2,'color',[cl cl cl]);
line([x(2) x(2)-dx],[y(2) y(2)+dy],'linewidth',lw2,'color',[cl cl cl]);
line([x(2) x(2)+dx],[y(2) y(2)+dy],'linewidth',lw2,'color',[cl cl cl]);

% Text labels
text(2*B,0.7*B,'Forced Kelvin wave','fontsize',fs,'FontAngle','italic');
text(1*B,0.3*B,'Reflected Kelvin wave','fontsize',fs,'FontAngle','italic');
text(0.25*B,0.6*B,'Poincare waves','fontsize',fs,'FontAngle','italic');

% Text labels for axes
text(fac*L-30,  30,'x','fontsize',fs,'FontAngle','italic');
text(       5,fac*B,'y','fontsize',fs,'FontAngle','italic');

% Make eps figure
if printen == 1;
    print(figure(1),'-dpng','-r300','doc/basinplot.png');
    close all;
end