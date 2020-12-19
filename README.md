# disk-to-tg

I had bunch of images which were on disk and this script moved them to a Telegram Group

## Data Layout

Currently, this is how the data was present:

```
- /opt/data
	- author-name-1
		- album-name-1
			- image-1
			- image-2
		- album-name-2
			- image-1
			- image-2
	- author-name-2
		- album-name-1
			- image-1
			- image-2		
```

## TG Format

## Upload

```shell script
main.py /opt/data
```