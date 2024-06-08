document.addEventListener('scroll', () =>{
    const elements = document.querySelectorAll('.title_text');
    const viewport = window.innerHeight;

    elements.forEach(element =>{
        const rect = element.getBoundingClientRect();
        const distanceFrom_view = Math.abs(rect.top - viewport/2);
        const max_dis = viewport/2;

        let new_size = Math.max(10, 50 - (distanceFrom_view / max_dis)*30);
        element.style.fontSize = new_size + 'px';
        
    });
});