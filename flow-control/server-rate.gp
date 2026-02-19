set datafile separator ","
set terminal pngcairo size 1280,720 enhanced font 'Arial,16'
set output "server-rate.png"

set xlabel "time (s)"
set ylabel "rate (kB/s, log10)"
set logscale y
set format y "10^{%L}"
set key top right

plot "server-stats.csv" using 1:($2/1000) with lines lw 3 title "CA", \
     "server-stats.csv" using 1:($3/1000) with lines lw 3 title "SMA", \
     "server-stats.csv" using 1:($4/1000) with lines lw 3 title "EMA"
