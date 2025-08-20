set datafile separator ","

set datafile separator ","
set terminal pngcairo size 1280,720 enhanced font 'Arial,16'
set output "rate.png"

set xlabel "time (s)"
set ylabel "rate (kpbs)"
unset key
plot "stats.csv" using 1:3 with lines lw 3 title "data"
