from helper.utils import handleURL
import uuid


# Parse reddit image,video,gallery image,multi-media content
def post_content(data, subm):
    if hasattr(subm, "poll_data"):
        return {"type": "Invalid", "data": []}
    else:
        # Multi [video+img] [media_metadata.id.e (check Image or RedditVideo)] [1anj4fi]
        hasMulti = data.get("media_metadata", "")
        isGallery = data.get("is_gallery", False)
        st = set()
        if hasMulti and not isGallery:
            for imageID in hasMulti:
                mediaType = hasMulti.get(imageID, {}).get("e", "")
                st.add(mediaType)
            if len(st) >= 2:
                final_data = []
                for imageID in hasMulti:
                    mediaType = hasMulti.get(imageID, {}).get("e", "")
                    if mediaType == "Image":
                        # gif
                        hasGif = (
                            hasMulti.get(imageID, {})
                            .get("variants", {})
                            .get("gif", {})
                            .get("resolutions", [])
                        )
                        if hasGif:
                            for objs in hasGif:
                                if objs.get("u", ""):
                                    objs["u"] = handleURL(objs["u"])

                            final_data.append(
                                {
                                    "type": "gif",
                                    "id": imageID,
                                    "data": sorted(hasGif, key=lambda x: x["y"]),
                                }
                            )
                        # image
                        else:
                            dat = hasMulti.get(imageID, {}).get("p", [])
                            for objs in dat:
                                if objs.get("u", ""):
                                    objs["u"] = handleURL(objs["u"])
                            sourceImage = hasMulti.get(imageID, {}).get("s", {})
                            if sourceImage:
                                dat.append(sourceImage)
                            if dat:
                                final_data.append(
                                    {
                                        "type": "image",
                                        "id": imageID,
                                        "data": sorted(dat, key=lambda x: x["y"]),
                                    }
                                )
                    # videos
                    elif mediaType == "RedditVideo":
                        dat = hasMulti.get(imageID, {})
                        if dat:
                            final_data.append(
                                {
                                    "type": "video",
                                    "id": imageID,
                                    "data": {
                                        "dash_url": handleURL(dat.get("dashUrl", "")),
                                        "hls_url": handleURL(dat.get("hlsUrl", "")),
                                    },
                                }
                            )

                return {"type": "multi", "data": final_data}

        # Gif [preview.variants.gif] [1an7ms7]
        if data.get("preview", {}):
            hasGif = (
                data.get("preview", {})
                .get("images")[0]
                .get("variants", {})
                .get("gif", {})
                .get("resolutions", [])
            )

            if hasGif:
                for objs in hasGif:
                    if objs.get("url", ""):
                        objs["url"] = handleURL(objs["url"])

                return {
                    "data": sorted(hasGif, key=lambda x: x["height"]),
                    "id": str(uuid.uuid4()),
                    "type": "gif",
                }

        # Video [secure_media.reddit_video.dash_url.hls_url.fallback_url.scrubber_media_url] [1alyf9i]
        val = data.get("secure_media", {})
        if val:
            hasVideo = data.get("secure_media", {}).get("reddit_video", {})
            # print(hasVideo, "hasVideo")
            if hasVideo:
                vid_data = {
                    "dash_url": handleURL(hasVideo.get("dash_url", "")),
                    "hls_url": handleURL(hasVideo.get("hls_url", "")),
                    "fallback_url": handleURL(hasVideo.get("fallback_url", "")),
                    "scrubber_media_url": handleURL(
                        hasVideo.get("scrubber_media_url", "")
                    ),
                }
                return {"data": vid_data, "type": "video", "id": str(uuid.uuid4())}

        # Image [preview.resolutions] [1amno06]
        if data.get("preview", {}):
            hasImage = data.get("preview", {}).get("images")[0].get("resolutions", [])
            if data:
                sourceImage = data.get("preview", {}).get("images")[0].get("source", {})
                for objs in hasImage:
                    if objs.get("url", ""):
                        objs["url"] = handleURL(objs["url"])
                if sourceImage:
                    hasImage.append(sourceImage)
                return {
                    "data": sorted(hasImage, key=lambda x: x["height"]),
                    "id": str(uuid.uuid4()),
                    "type": "image",
                }

        # Gallery [media_metadata.id.p] [1anhgwz]
        hasGallery = data.get("media_metadata", "")
        imageGallery = []
        if hasGallery:
            for imageID in hasGallery:
                imgs = hasGallery.get(imageID, {}).get("p", [])
                if imgs:
                    for objs in imgs:
                        if objs.get("u", ""):
                            objs["u"] = handleURL(objs["u"])
                    sourceImage = hasGallery.get(imageID, {}).get("s", {})
                    if sourceImage:
                        imgs.append(sourceImage)
                    imageGallery.append({"id": imageID, "pics": imgs})

            if imageGallery:
                for objs in imageGallery:
                    getPics = objs.get("pics", [])
                    if getPics:
                        objs.get("pics", []).sort(key=lambda x: x["y"])

            return {
                "data": imageGallery,
                "type": "gallery",
                "id": str(uuid.uuid4()),
            }

        return {"type": "text", "data": []}
