function resize_images() {
    var myImgs = document.getElementsByClassName('partimg');

    for (var i = 0; i < myImgs.length; i++) {
        //style = window.getComputedStyle(myImgs[i],null);
        //var dpi = style.getPropertyValue('--image-dpi');
        //if (dpi != "") {
            // wait for the image to load
            //console.log("hello" + dpi + "hello")
        //    while (typeof myImgs[i].naturalWidth !== "undefined" && myImgs[i].naturalWidth === 0) { ; }

            // scale it correctly for its dpi
            myImgs[i].width = myImgs[i].naturalWidth * 96.0/600;
            myImgs[i].height = myImgs[i].naturalHeight * 96.0/600;
        //}
    }
}
