#include <iostream>

template <typename T>
__attribute__((used, noinline, annotate("patch_point"))) T myPathPoint(T a,
                                                                       T b) {
  return a + b;
}



int main() {
  static constexpr int myArray[]{1, 4, 5, 6, 10};
  int mySum{0};
  for (const auto &el : myArray) {
    mySum += el * myPathPoint(mySum, el);
  }
  std::cout << "Sum of my array: " << mySum << std::endl;
  return 0;
}