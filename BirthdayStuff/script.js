document.addEventListener("DOMContentLoaded", () => {
    const pages = [
        document.getElementById("firstPage"),
        document.getElementById("secondPage"),
        document.getElementById("thirdPage")
    ];

    const topArrow    = document.getElementById("topArrow");
    const bottomArrow = document.getElementById("bottomArrow");

    let currentPage = 0;
    let isAnimating = false;

    // Animation duration must match CSS (450ms)
    const ANIM_DURATION = 450;

    /* ── Arrow active (click feedback) ── */
    function flashArrow(arrowEl) {
        arrowEl.classList.add("active");
        setTimeout(() => arrowEl.classList.remove("active"), 300);
    }

    /* ── Update arrow visibility at page ends ── */
    function updateArrows(index) {
        // Top arrow: hidden on first page
        if (index === 0) {
            topArrow.classList.add("edge-hidden");
        } else {
            topArrow.classList.remove("edge-hidden");
        }
        // Bottom arrow: hidden on last page
        if (index === pages.length - 1) {
            bottomArrow.classList.add("edge-hidden");
        } else {
            bottomArrow.classList.remove("edge-hidden");
        }
    }

    /* ── Core page transition ── */
    function showPage(nextIndex, direction) {
        // direction: 1 = going forward (down), -1 = going back (up)
        if (isAnimating || nextIndex === currentPage) return;
        if (nextIndex < 0 || nextIndex >= pages.length) return;

        isAnimating = true;

        const outPage = pages[currentPage];
        const inPage  = pages[nextIndex];

        // Determine animation classes
        const outClass = direction === 1 ? "slide-out-up"   : "slide-out-down";
        const inClass  = direction === 1 ? "slide-in-up"    : "slide-in-down";

        // Animate OUT the current page
        outPage.classList.add(outClass);

        // Show and animate IN the next page
        inPage.classList.remove("hidden");
        inPage.classList.add("shown", inClass);

        setTimeout(() => {
            // Clean up outgoing page
            outPage.classList.remove("shown", outClass);
            outPage.classList.add("hidden");

            // Clean up incoming page animation class
            inPage.classList.remove(inClass);

            currentPage = nextIndex;
            isAnimating = false;
            updateArrows(currentPage);
        }, ANIM_DURATION);
    }

    /* ── Arrow clicks ── */
    bottomArrow.addEventListener("click", () => {
        if (currentPage < pages.length - 1) {
            flashArrow(bottomArrow);
            showPage(currentPage + 1, 1);
        }
    });

    topArrow.addEventListener("click", () => {
        if (currentPage > 0) {
            flashArrow(topArrow);
            showPage(currentPage - 1, -1);
        }
    });

    /* ── Scroll / wheel navigation ── */
    let scrollCooldown = false;
    window.addEventListener("wheel", (e) => {
        if (scrollCooldown || isAnimating) return;
        scrollCooldown = true;
        setTimeout(() => { scrollCooldown = false; }, ANIM_DURATION + 100);

        if (e.deltaY > 0 && currentPage < pages.length - 1) {
            flashArrow(bottomArrow);
            showPage(currentPage + 1, 1);
        } else if (e.deltaY < 0 && currentPage > 0) {
            flashArrow(topArrow);
            showPage(currentPage - 1, -1);
        }
    }, { passive: true });

    /* ── Touch swipe navigation ── */
    let touchStartY = 0;
    window.addEventListener("touchstart", (e) => {
        touchStartY = e.touches[0].clientY;
    }, { passive: true });

    window.addEventListener("touchend", (e) => {
        if (isAnimating) return;
        const delta = touchStartY - e.changedTouches[0].clientY;
        if (Math.abs(delta) < 40) return; // too small a swipe

        if (delta > 0 && currentPage < pages.length - 1) {
            flashArrow(bottomArrow);
            showPage(currentPage + 1, 1);
        } else if (delta < 0 && currentPage > 0) {
            flashArrow(topArrow);
            showPage(currentPage - 1, -1);
        }
    }, { passive: true });

    /* ── Init ── */
    updateArrows(0);
});