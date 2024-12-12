function basinnofriction;

fclose all;
close all;
clc;

% Print?
printen      = 1;

% Geometry
B            =  550;
L            = 1800;

% Load analytical solution
load('basinnofrictionexact.mat');
xana         = xana/1e3;
yana         = yana/1e3;
[xana,yana]  = meshgrid(xana,yana);
yana         = yana + B/2;

% Read the map-file for each of the three models
map1         = ['../c020_basinnofriction_squares/dflowfmoutput/basinsquares_map.nc'];
map2         = ['../c021_basinnofriction_squaresfine/dflowfmoutput/basinsquaresfine_map.nc'];
map3         = ['../c022_basinnofriction_triangles/dflowfmoutput/basintriangles_map.nc'];
h1           = nc_varget(map1,'s1');
h2           = nc_varget(map2,'s1');
h3           = nc_varget(map3,'s1');
for i=1:size(h1,2);
    hmax1(i) = max(h1(:,i));
end
for i=1:size(h2,2);
    hmax2(i) = max(h2(:,i));
end
for i=1:size(h3,2);
    hmax3(i) = max(h3(:,i));
end
x1           = nc_varget(map1,'FlowElem_xcc');
x2           = nc_varget(map2,'FlowElem_xcc');
x3           = nc_varget(map3,'FlowElem_xcc');
y1           = nc_varget(map1,'FlowElem_ycc');
y2           = nc_varget(map2,'FlowElem_ycc');
y3           = nc_varget(map3,'FlowElem_ycc');

% Read solution
G1           = dflowfm.readNet(map1);
G2           = dflowfm.readNet(map2);
G3           = dflowfm.readNet(map3);
D1           = hmax1;
D2           = hmax2;
D3           = hmax3;

% Plot first solution
figure(1);
hold on;
fac          = 1.3;
xsol1        = G1.cor.x/1e3;
ysol1        = G1.cor.y/1e3 + fac.*B;
h            = trisurfcorcen(G1.tri,xsol1,ysol1,D1(G1.map3),D1(G1.map3));
set(h,'edgeColor','none');
xsol2        = G2.cor.x/1e3;
ysol2        = G2.cor.y/1e3 + fac.*B;
h            = trisurfcorcen(G2.tri,xsol2,ysol2,D2(G2.map3),D2(G2.map3));
set(h,'edgeColor','none');
xsol3        = G3.cor.x/1e3;
ysol3        = G3.cor.y/1e3 + fac.*B;
h            = trisurfcorcen(G3.tri,xsol3,ysol3,D3(G3.map3),D3(G3.map3));
set(h,'edgeColor','none');
view(0,90);
axis off;
hold off;
hold on;
pcolor(xana,yana,hana);
shading flat;
caxis([0 3.0]);
clb = colorbar;
set(clb,'ytick',[0:0.5:3.0]);
hold off;

% Print
if printen == 1;
    print(figure(1),'-dpng','-r300','doc/basinnofriction.png');
    close all;
end