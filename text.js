document.addEventListener('scroll', () =>{
    const elements = document.querySelectorAll('.body_text');
    const viewport = window.innerHeight;

    elements.forEach(element =>{
        const rect = element.getBoundingClientRect();
        const distanceFrom_view = Math.abs(rect.top - viewport/2);
        const max_dis = viewport/4;

        let new_size = Math.max(10, 50 - (distanceFrom_view / max_dis)*30);
        let color = 'rgb'+(250 - new_size*2, 235 - new_size*2, 215 - new_size*2);
        element.style.color = color;
        
    });
});