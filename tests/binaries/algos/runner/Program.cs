using System;
using System.Collections.Generic;
using Algorithms;
  

namespace AlgoTest {
      

    class Algos {
          

        static void Main(string[] args)
        {

            var comparer = Comparer<int>.Create((s1, s2) => s1.CompareTo(s2));
            List<int> sortThis = new List<int>()
            {
                4, 2, 1, 6, 8, 3
            };
            Algorithms.Sorting.BubbleSorter.BubbleSort(sortThis);
            
            var x =Algorithms.Numeric.CatalanNumbers.GetNumber(50);


            foreach (var num in sortThis)
            {
                Console.WriteLine(num);
            }
            Console.WriteLine(x);

        }
    }
}