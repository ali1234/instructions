#declare AL_LIGHT_COL = 0.5;
#declare AL_LIGHT_NUM = 7;

light_source {
        <0,-1500,0> + L3ModelBBoxCenter
        color rgb <AL_LIGHT_COL,AL_LIGHT_COL,AL_LIGHT_COL>
        area_light <2500, 0, 0>, <0, 0, 2500>, AL_LIGHT_NUM, AL_LIGHT_NUM
        jitter
        adaptive 1
}

light_source {
        <1500,-750,0> + L3ModelBBoxCenter
        color rgb <AL_LIGHT_COL,AL_LIGHT_COL,AL_LIGHT_COL>
        area_light <0,0,1500>, <0,1500,0>, AL_LIGHT_NUM, AL_LIGHT_NUM
        jitter
        adaptive 1
}

light_source {
        <-1500,-750,0> + L3ModelBBoxCenter
        color rgb <AL_LIGHT_COL,AL_LIGHT_COL,AL_LIGHT_COL>
        area_light <0,0,1500>, <0,1500,0>, AL_LIGHT_NUM, AL_LIGHT_NUM
        jitter
        adaptive 1
}

light_source {
        <0,-750,1500> + L3ModelBBoxCenter
        color rgb <AL_LIGHT_COL,AL_LIGHT_COL,AL_LIGHT_COL>
        area_light <1500,0,0>, <0,1500,0>, AL_LIGHT_NUM, AL_LIGHT_NUM
        jitter
        adaptive 1
}

light_source {
        <0,-750,-1500> + L3ModelBBoxCenter
        color rgb <AL_LIGHT_COL,AL_LIGHT_COL,AL_LIGHT_COL>
        area_light <1500,0,0>, <0,1500,0>, AL_LIGHT_NUM, AL_LIGHT_NUM
        jitter
        adaptive 1
}




global_settings { ambient_light rgb<0.4, 0.3, 0.2> }
