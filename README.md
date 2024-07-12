# DMC1 Resource Repacker

## Depency:
* Python 3

## Usage:
* ### Fsd/Dat/Itm Files:

   #### Unpack:
    ```bash
    $ python3 dataRepack.py <file>
    ```
    #### Repack:
    ```bash
    $ python3 dataRepack.py -p <file>
    ```

* ### Texture Files:

    #### Unpack:
    ```bash
    $ python3 textureRepack.py <texturefile>
    ```
    #### Repack:
    ```bash
    $ python3 textureRepack.py -p <texturefile>
    ```

    #### Supported texture files:
    - .tm2
    - .ip2
    - .t32

* ### MSG Files:
  
    ```
    ---- MSG Repacker (DMC 1) ----
    ---- by deadYokai         ----

    ---- Usage: python3 msg.py [options] <filename>

    ---- Options:
         -e      Extract msg to txt (default option)
         -p      Pack txt to msg
         -c      Charset file (default: charindex.txt)
    ```

