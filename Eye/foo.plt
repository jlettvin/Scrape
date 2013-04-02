set terminal png nocrop enhanced font verdana 12 size 640,480
set dgrid3d
set title "Resolver Gnuplot Demo"
set xlabel "X axis"
set xlabel  offset character -2, -2, 0
set ylabel "Y axis"
set ylabel  offset character 2, -2, 0
set zlabel "Z axis"
set zlabel  offset character 1, 0, 0
set output "test.png"
set contour both
set view 45, 30
#set style data lines
set hidden3d
splot 'graph/E5.0e1.0r0.05.dat'
#splot "-" title "The Data"
