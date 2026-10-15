import { useState, useEffect } from 'react'
import { useT } from './i18n'
import forestCanopy from './assets/backgrounds/forest-canopy.jpg'
import mountainRiver from './assets/backgrounds/mountain-river.jpg'
import seaArch from './assets/backgrounds/sea-arch.jpg'
import alpineValley from './assets/backgrounds/alpine-valley.jpg'
import summitPeak from './assets/backgrounds/summit-peak.jpg'
import peakMonochrome from './assets/backgrounds/peak-monochrome.jpg'

const IMAGES = [
  { src: forestCanopy, credit: 'Kristaps Ungurs' },
  { src: mountainRiver, credit: 'Hendrik Cornelissen' },
  { src: seaArch, credit: 'Sebastian Boring' },
  { src: alpineValley, credit: 'Kalen Emsley' },
  { src: summitPeak, credit: 'Rohit Tandon' },
  { src: peakMonochrome, credit: 'Kerensa Pickett' },
]
const ROTATE_MS = 12000

// Full-bleed background behind the frosted-glass .card, crossfading between
// a few bundled photos. Purely decorative (aria-hidden) and non-interactive,
// aside from the small photo-credit caption required by their license.
export default function PageBackground() {
  const { t } = useT()
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setIndex(i => (i + 1) % IMAGES.length), ROTATE_MS)
    return () => clearInterval(id)
  }, [])

  return (
    <>
      <div className="page-backgrounds" aria-hidden="true">
        {IMAGES.map((img, i) => (
          <div
            key={img.src}
            className={`page-backgrounds__item${i === index ? ' page-backgrounds__item--active' : ''}`}
            style={{ backgroundImage: `url(${img.src})` }}
          />
        ))}
      </div>
      <p className="page-backgrounds__credit">
        {t('footer.photoCredit', { name: IMAGES[index].credit })}
      </p>
    </>
  )
}
