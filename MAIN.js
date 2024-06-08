console.log("PROGRAM STARTED")
var curr_text_size = function(amount){
    var scroll_top = (window.scrollY || document.scroll_top);
    var size = 90 - ((scroll_top / amount) || 0);
    console.log(size)
    if (size <= 15) size = 15;

    document.querySelector('.title_text').setAttribute('style', 'font size: '+size+'px');

};
window.addEventListener('scroll', function(){ curr_text_size(10)});