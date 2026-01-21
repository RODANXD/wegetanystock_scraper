import React from 'react';
import cleaned_products from '../data/cleaned_products.json';

const ProductList = () => (
  <section className="min-h-screen  py-10">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h2 className="text-4xl font-extrabold text-shadow-indigo-900 mb-10 text-center">
        Product Clean Preview
      </h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-6">
        {cleaned_products.map((p) => (
          <article
            key={p.id ?? p.cleaned_name}
            className="group relative bg-white rounded-2xl shadow hover:shadow-lg transition-all duration-300 overflow-hidden"
          >
            {/* Badge for quick scan */}
            <span className="absolute top-3 left-3 z-10 bg-indigo-600 text-white text-sm font-semibold px-2 py-1 rounded-full">
              {p.brand}
            </span>

            {/* Image */}
            <div className="aspect-square w-full overflow-hidden">
              <img
                src={p.image_url}
                alt={p.cleaned_name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
            </div>

            {/* Content */}
            <div className="p-4">
              <h3 className="text-gray-900 font-semibold text-base ">
                {p.cleaned_name}
              </h3>

              <div className="mt-2 flex items-baseline justify-between">
                <span className="text-2xl font-bold text-green-600 flex">
                  <p className='text-indigo-700'>Price - </p>  {p.price || 'N/A'}
                </span>
              </div>
              <div className="">
                 <span className="text-xs text-gray-500">
                  Volume/Weight - {p.volume_weight}
                </span>
              </div>

             
              
            </div>
          </article>
        ))}
      </div>
    </div>
  </section>
);

export default ProductList;