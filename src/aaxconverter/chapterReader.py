
# Some magic: we parse the .json generated by audible-cli.
# to get the output structure like the one generated by ffprobe,
# we use some characters (#) as placeholder, add some new lines,
# put a ',' after the start value, we calculate the end of each chapter
# as start+length, and we convert (divide) the time stamps from ms to s.
# Then we delete all ':' and '/' since they make a filename invalid.
def main():
  pass


if __name__ == "__main__":
  main()

  # Duration: 05:56:14.97, start: 0.000000, bitrate: 64 kb/s
  # Chapters:
  #   Chapter #0:0: start 0.000000, end 878.875283
  #     Metadata:
  #       title           : Chapter 1
  #   Chapter #0:1: start 878.875283, end 1341.974059
  #     Metadata:
  #       title           : Chapter 2
  #   Chapter #0:2: start 1341.974059, end 1688.647982
  #     Metadata:
  #       title           : Chapter 3
  #   Chapter #0:3: start 1688.647982, end 2108.000363
  #     Metadata:
  #       title           : Chapter 4
  #   Chapter #0:4: start 2108.000363, end 2649.907664
  #     Metadata:
  #       title           : Chapter 5
  #   Chapter #0:5: start 2649.907664, end 2941.503855
  #     Metadata:
  #       title           : Chapter 6
  #   Chapter #0:6: start 2941.503855, end 3426.336508
  #     Metadata:
  #       title           : Chapter 7
  #   Chapter #0:7: start 3426.336508, end 3764.140408
  #     Metadata:
  #       title