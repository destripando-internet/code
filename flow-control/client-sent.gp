set datafile separator ","
set terminal pngcairo size 1280,720 enhanced font 'Arial,16'
set output "client-sent.png"

set xlabel "time (s)"
set ylabel "data (MB)"
set format y "%.1s"
unset key
plot "client-stats.csv" using 1:2 with lines lw 3 title "data"
